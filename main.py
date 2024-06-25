from kicktipp.scraper import get_current_standings

if __name__ == "__main__":
	df = get_current_standings()
	print(df.head())
