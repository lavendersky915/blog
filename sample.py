import requests
import json

CRUNCHBASE_API = "4b8fqdgv8ump7a7fftah8cfc"
def get_sample():
	COMPANY_NAME = 'Lumileds' # apple, google, facebook, acer
	url = "http://api.crunchbase.com/v/1/company/"+COMPANY_NAME+".js?api_key=" + CRUNCHBASE_API
	data = requests.get(url)
	json_data = data.json()
	#print json.dumps(json_data, indent=4)
	ERR = None
	COUNTRY_CODE = None
	try:
		ERR = json_data['error']
		print "====>>>> error ", ERR
	except:
		print "------->>>>> JSON_DATA"
		print json_data
		print "------->>>>> JSON_DATA"
	try:
		COUNTRY_CODE = json_data["offices"][0]["country_code"]
		print "---->>>> country code is ", COUNTRY_CODE
	except:
		print "OOPS, no country code."
get_sample()