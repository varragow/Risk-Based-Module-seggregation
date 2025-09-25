import subprocess
import json
import os
import logging

# Setup logging
log_file = os.path.join(os.getcwd(), "task_runner.log")
if os.path.exists(log_file):
    os.remove(log_file)
    print(">> Removed existing task_runner.log file")
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def log_and_print(message):
    print(message)
    logging.info(message)

try:
    # Load config
    state_file = os.path.join(os.getcwd(), "config.json")
    with open(state_file, "r") as file:
        data = json.load(file)

    if data.get('execution_status') == 1:
        log_and_print("Execution status is 1. Running clustering algorithm...")
        result = subprocess.run(["python", "clustering_algorithm_newVersion.py"], capture_output=True, text=True)
        print("Clustering Output:\n" + result.stdout)
        logging.info("Clustering Output:\n" + result.stdout)
        print("\n >> Reload the dashboard !!!")
        if result.stderr:
            logging.error("Clustering Errors:\n" + result.stderr)
    else:
        log_and_print("Execution status is not 1. Skipping clustering algorithm.")

except Exception as e:
    logging.error("Exception occurred: " + str(e))
    print("An error occurred. Check logs for details.")