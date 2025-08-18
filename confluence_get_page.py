# This script returns json information about the content from confluence
# This script also returns json information about the particular content id
# with body expanded.
import csv
import os
import requests
import re
import json
import logging
import base64
from bs4 import BeautifulSoup
import getpass
from cryptography.fernet import Fernet

def main():
	path=r'\\rover\cts\Axiom\Executables\ModuleVsTechArea_Data'
	#disable warnings
	requests.packages.urllib3.disable_warnings()

	#SMSESSSION url
	smSessionURL = "https://sm-sts.qualcomm.com/smapi/rest/createsmsession?hostname=confluence.qualcomm.com"

	#rest api server url
	confluenceServerURL = "https://confluence.qualcomm.com/confluence"

	#service account user name

	# Generate a key
	key = Fernet.generate_key()
	cipher = Fernet(key)
	username=input("Enter username:")
	password = getpass.getpass("Enter your password:").encode()
	encrypted = cipher.encrypt(password)

	smSessionHeaders = {'Accept' : 'application/json'}

	#get page information
	pageTitle = "Module vs Tech Area"
	spaceKey = "APTPlatform"
	getPageURL="/rest/api/content?title="+pageTitle+"&spaceKey="+spaceKey+"&expand=body.storage"

	#setting configuration details for logging
	logging.basicConfig()

	#logger info
	logger = logging.getLogger('conf_rest_get_page')
	logger.setLevel(logging.DEBUG)

	#log file
	fileHandler = logging.FileHandler('conf_rest_get_page.log')
	fileHandler.setLevel(logging.DEBUG)

	#adding file handler to logger
	logger.addHandler(fileHandler)

	#format
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	fileHandler.setFormatter(formatter)

	logger.info('--------------Getting page from confluence--------------------------')

	try:
		#get SMSESSION cookie
		response = requests.get(smSessionURL,verify=False, headers=smSessionHeaders, auth=(username, f"{cipher.decrypt(encrypted).decode()}"))
		logger.debug('Getting SMSESSION from URL %s', response.url)

		if response.status_code == 200:
			smSessionJson = response.json()
		else:
			logger.error("Error while obtaining SMSESSION %s ", response.status_code)
			logger.error(response.text)

		cookie = smSessionJson[u'SMSESSION']

		#headers
		headers = {'Cookie' : 'SMSESSION=%s' % cookie}

		#get page
		response = requests.get(confluenceServerURL+getPageURL, verify=False, headers=headers)
		logger.debug('URL for getting confluence page is %s', response.url)

		if response.status_code == 200:
			json = response.json()
			# logger.info("JSON for the page  is %s",json)
			page_content = json['results'][0]['body']['storage']['value']
			soup = BeautifulSoup(page_content, 'html.parser')
			h1_tags = soup.find_all('h1')

			for file_name in os.listdir(path):
				if file_name.endswith(".csv"):
					file_path=os.path.join(path,file_name)
					os.remove(file_path)
					print(f">> Removed {file_name} from {file_path} successfully")
			for h1 in h1_tags:
				my_list=[]
				heading_text = h1.get_text(strip=True)
				print(f"\nHeading: {heading_text}")

				# Find the next <table> after this <h1>
				table = h1.find_next('table')
				if table:
					rows = table.find_all('tr')
					with open(os.path.join(path,f"{heading_text}.csv"), 'w', newline='', encoding='utf-8') as csvfile:
						writer = csv.writer(csvfile)
						for row in rows:
							cells = row.find_all(['th', 'td'])
							cell_text = [cell.get_text(strip=True) for cell in cells]
							print(cell_text)
							my_list.append(cell_text)
						# print(my_list)
						print(f"Creating {os.path.join(path,heading_text)}.csv")
						writer.writerows(my_list)

		else:
			logger.error("Error while obtaining page with given page title %s ", response.status_code)
	except Exception as e:
		logger.error("Error while obtaining page with given page title %s due to %s",pageTitle,str(e))

if __name__ == '__main__':
    main()
