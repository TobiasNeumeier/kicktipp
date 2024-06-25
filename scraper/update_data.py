import logging
import schedule
import time

from firebase_utils import write_dataframe_to_firestore
from scraper.util import setup_browser, read_all_days


logger = logging.getLogger(__name__)


# Example function to update data in Firestore
def update_data(browser=None):
	if not browser:
		browser = setup_browser(headless=True)
	df = read_all_days(browser)
	write_dataframe_to_firestore(df, "all_bets")
	logger.info("Updated data successfully!")


# Schedule the update_data function to run every 15 minutes
schedule.every(15).minutes.do(update_data)


def run_scheduler():
	while True:
		schedule.run_pending()
		time.sleep(1)


if __name__ == '__main__':
	update_data()  # Run once at the start
	run_scheduler()
