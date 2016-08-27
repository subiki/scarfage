#!/usr/bin/env python

import httplib, json, csv
import requests
import sys

#
# import from scarfage json the latest scarf data.
# send data in CSV format to stdout.
#
# Usage: ./import.py >> scarfDB.csv
#


# format image url
# given a scarfage image id from json, returns a url to the image
def image_url(image_id):
    return "https://www.scarfage.com/image/"+str(image_id)+"/full"

#retrieve scarf image, and save in local folder named 'testimgs'
def save_image_locally(image_id, con):
    img_data = requests.get(image_url(image_id)).content
    with open('testimgs/'+str(image_id)+'.jpg', 'wb') as handler:
        handler.write(img_data)

# get the scarfage json
scarfjson_url = "/item/search?page=&limit=999&query=&sort=name"
headers = {"Accept": "application/json"}

conn = httplib.HTTPSConnection("www.scarfage.com")
conn.request("GET", scarfjson_url, '', headers)
response = conn.getresponse()

data = json.loads(response.read())['results']

output = csv.writer(sys.stdout)

for scarf in data:
    for i in range(len(scarf['images'])):
        save_image_locally(scarf['images'][i], conn)
        scarf['images'][i] = image_url(scarf['images'][i])

conn.close()

output.writerow(data[0].keys()) # header row

for row in data:
    output.writerow(row.values())
