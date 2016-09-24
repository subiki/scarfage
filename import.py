#!/usr/bin/env python
# -*- coding: utf-8 -*-

import httplib, json, csv
import requests
import sys

#
# import from scarfage json the latest scarf data.
# save data in CSV format to stdout.
#
# Usage: ./import.py {-n NUM} >> scarfDB.csv
# retrieves NUM latest (default 999) scarves frolm scarfage.com
#
NUM = '999' #set to 999 to get everything. Query requests most recent NUM entries
if len(sys.argv) > 1 and sys.argv[1] == '-n':
    NUM = sys.argv[2]

# format json for print
def get_pretty_print(json_object):
    return json.dumps(json_object, sort_keys=True, indent=4, separators=(',', ': '))

# format image url
def image_url(image_id):
    return "https://www.scarfage.com/image/"+str(image_id)+"/full"

#retrieve scarf image, and save in local folder named 'testimgs'
def save_image_locally(image_id, con):
    img_data = requests.get(image_url(image_id)).content
    with open('testimgs/'+str(image_id)+'.jpg', 'wb') as handler:
        handler.write(img_data)

# get the scarfage json
scarfjson_url = "/item/search?page=&limit="+NUM+"&query=&sort=added"
headers = {"Accept": "application/json"}

conn = httplib.HTTPSConnection("www.scarfage.com")
conn.request("GET", scarfjson_url, '', headers)
response = conn.getresponse()
data = json.loads(response.read())['results']
# print get_pretty_print(data)

output = csv.writer(sys.stdout)
output.writerow([ 'Name', 'Description', 'Tags', 'Added', 'Image0', 'Image1', 'ID' ]) # header row

for scarf in data:
    # get single scarf record (with description)
    scarfjson_url = "/item/" + str(scarf['uid'])
    conn.request("GET", scarfjson_url, '', headers)
    response = conn.getresponse()
    scarfdata = json.loads(response.read())

    scarfdata['image1'] = ""
    scarfdata['image0'] = ""
    for i in range(len(scarfdata['images'])):
        # uncomment next line to pull EVERY image to your local folder
        # save_image_locally(scarf['images'][i], conn)
        scarfdata['image'+str(i)] = image_url(scarfdata['images'][i])

    # print get_pretty_print(scarfdata)
    output.writerow([
        scarfdata['name'],
        scarfdata['body'].encode('utf-8'),
        scarfdata['tags'],
        scarfdata['added'],
        scarfdata['image0'],
        scarfdata['image1'],
        scarfdata['uid'],
    ])

conn.close()
