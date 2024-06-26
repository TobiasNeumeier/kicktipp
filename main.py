import threading
import app
from scraper import update_data


# Function to run the Dash app
def run_dash_app():
	app.app.run_server(host="localhost", debug=False, use_reloader=False, port=8080)


# Function to run the update data scheduler
def run_data_updater():
	update_data.run_scheduler()


if __name__ == '__main__':
	# Create threads for the Dash app and data updater
	dash_thread = threading.Thread(target=run_dash_app)
	updater_thread = threading.Thread(target=run_data_updater)
	
	# Start both threads
	dash_thread.start()
	updater_thread.start()
	
	# Join both threads to the main thread
	dash_thread.join()
	updater_thread.join()
