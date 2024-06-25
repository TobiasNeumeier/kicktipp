import re
from io import StringIO
import logging

import pandas as pd
from bs4 import BeautifulSoup
from helium import start_chrome

from firebase_utils import write_dataframe_to_firestore

logger = logging.getLogger(__name__)

GAME_DAYS = range(1, 12)
SCORE_PATTERN = r"\d+:\d+"


def setup_browser(headless=True):
	baseurl = "https://www.kicktipp.de/darkest-em2024/tippuebersicht?tippsaisonId=2582539"
	browser = start_chrome(baseurl, headless=headless)
	return browser


def get_soup(browser, day):
	url = f"https://www.kicktipp.de/darkest-em2024/tippuebersicht?tippsaisonId=2582539&spieltagIndex={day}"
	browser.get(url)
	html = browser.page_source
	soup = BeautifulSoup(html, 'html.parser')
	return soup


def clean_table(_table, remove_tags=None):
	if remove_tags is None:
		remove_tags = ["sub"]

	for td in _table.find_all("td"):
		for remove_tag in remove_tags:
			for tag in td.find_all(remove_tag):
				tag.decompose()
	return _table


def parse_actual_score(text: str) -> str:
	matches = re.findall(SCORE_PATTERN, text)
	if matches:
		return matches[0]
	elif "-:-" in text:
		return "-:-"
	else:
		logger.warning(f"Could not parse score from string: {text}")
		return "-:-"


def parse_game_name(text: str) -> str:
	return f"{text[:3]} - {text[3:6]}"


def unpivot_game_columns(_df: pd.DataFrame) -> pd.DataFrame:
	unpivot_columns = [col for col in _df.columns if col != "Name"]
	return _df.melt(id_vars=["Name"], value_vars=unpivot_columns, var_name="Game", value_name="Tip")


def read_and_process_single_day(_soup, day: int) -> pd.DataFrame:
	tables = _soup.find_all("table")
	# we are looking for the second table
	cleaned_table = clean_table(tables[1])
	# wrap html in StringIO
	cleaned_table = StringIO(str(cleaned_table))
	return (
		pd.read_html(cleaned_table)[0]
		.pipe(drop_non_interesting_columns)
		.pipe(drop_empty_rows)
		.pipe(unpivot_game_columns)
		.assign(**{
			"Actual Score": lambda _df: _df["Game"].apply(parse_actual_score),
			"Game": lambda _df: _df["Game"].apply(parse_game_name),
			"Day": day
		})
	)


def drop_non_interesting_columns(_df):
	df = (
		_df.loc[:, ~_df.columns.str.contains('^Unnamed')]
		.drop(columns=["+/-", "P", "B", "S", "G", "Pos"])
	)
	
	# Function to check if a column name contains any letters
	def contains_letters(column_name):
		return bool(re.search('[a-zA-Z]', column_name))
	
	columns_with_letters = [col for col in df.columns if contains_letters(col)]
	df = df[columns_with_letters]
	
	return df


def drop_empty_rows(_df):
	return _df.dropna(how='all')


def read_all_days(browser) -> pd.DataFrame:
	df = pd.DataFrame()
	for day in GAME_DAYS:
		soup = get_soup(browser, day)
		df_day = read_and_process_single_day(soup, day)
		df = pd.concat([df, df_day])
	return df.reset_index(drop=True)


def get_current_standings(browser):
	df = read_all_days(browser)
	return (
		df.melt(id_vars=["Name"], value_vars=[x for x in df.columns if x != "Name"], var_name="Match", value_name="Tip")
		.query("Tip != '-:-'")
		.dropna(subset=["Tip"])
		.groupby("Name")["Tip"].agg(**{
			"Total Tips Submitted": "count",
			"V-Mann Count": lambda x: ((x == "2:1") | (x == "1:2")).sum()
		})
		.assign(**{
			"Total Tips Possible": lambda _df: max(_df["Total Tips Submitted"]),
			"V-Mann Relative Frequency": lambda _df: _df["V-Mann Count"] / _df["Total Tips Possible"]
		})
		.sort_values("V-Mann Count", ascending=False)
	)
