import pandas as pd
from bs4 import BeautifulSoup
from helium import start_chrome

GAME_DAYS = range(12)


def setup_browser():
	baseurl = "https://www.kicktipp.de/darkest-em2024/tippuebersicht?tippsaisonId=2582539"
	browser = start_chrome(baseurl)
	return browser


def get_soup(browser, day=1):
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


def read_and_process_df(_soup, day):
	tables = _soup.find_all("table")
	cleaned_table = clean_table(tables[1])
	return (
		pd.read_html(str(cleaned_table))[0]
		.pipe(drop_uninteresting_columns)
		.pipe(drop_empty_rows)
		# .assign(game_day=day)
	)


def drop_uninteresting_columns(_df):
	return (
		_df.loc[:, ~_df.columns.str.contains('^Unnamed')]
		.drop(columns=["+/-", "P", "B", "S", "G"])
	)


def drop_empty_rows(_df):
	return _df.dropna(how='all')


def read_all_days() -> pd.DataFrame:
	browser = setup_browser()
	df = pd.DataFrame()
	for day in GAME_DAYS:
		soup = get_soup(browser, day)
		df_day = read_and_process_df(soup, day=day)
		if df.empty:
			df = df_day
		else:
			df = df.merge(df_day, how="left", on="Name")
	return df


def display_current_standings():
	df = read_all_days()
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
