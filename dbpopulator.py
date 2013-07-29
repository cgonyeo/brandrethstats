#!/usr/bin/python

import httplib2
import sys,zipfile,re,os,csv

from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from oauth2client.client import OAuth2WebServerFlow
from apiclient import errors
from openpyxl import Workbook
from openpyxl import load_workbook
from pyquery import PyQuery as pq
from lxml.cssselect import CSSSelector

BrandrethSpreadsheetName = 'Brandreth Guest Books'

def authenticateUser():
	# Copy your credentials from the APIs Console
	CLIENT_ID = '461198277388-s5p2aps1d23005tgjasb6ihbmnc1va9v.apps.googleusercontent.com'
	CLIENT_SECRET = 'BkZbOMhTil0DFPxZ1FWT2Da3'

	# Check https://developers.google.com/drive/scopes for all available scopes
	OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive'

	# Redirect URI for installed apps
	REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

	# Path to the file to upload
	FILENAME = 'document.txt'

	# Run through the OAuth flow and retrieve credentials
	flow = OAuth2WebServerFlow(CLIENT_ID, CLIENT_SECRET, OAUTH_SCOPE, REDIRECT_URI)
	authorize_url = flow.step1_get_authorize_url()
	print 'Go to the following link in your browser: ' + authorize_url
	code = raw_input('Enter verification code: ').strip()
	print 'Authenticating with Google'
	credentials = flow.step2_exchange(code)

	# Create an httplib2.Http object and authorize it with our credentials
	http = httplib2.Http()
	http = credentials.authorize(http)

	drive_service = build('drive', 'v2', http=http)

	if drive_service is None:
		print 'Error creating drive service!'
	return drive_service

def lookForFile(drive_service, filename):
	result = []
	page_token = None
	while True:
		try:
			param = {}
			if page_token:
				param['pageToken'] = page_token
			files = drive_service.files().list(**param).execute()

			result.extend(files['items'])
			page_token = files.get('nextPageToken')
			if not page_token:
				break
		except errors.HttpError, error:
			print 'An error occured: %s' % error
			break
	for item in result:
		if item['title'] == filename:
			return item

# From: http://python-example.blogspot.com/2012/10/how-to-convert-ods-to-csv.html
def ods2csv(filepath):

    xml = zipfile.ZipFile(filepath).read('content.xml')

    def rep_repl(match):
	return '<table:table-cell>%s' %match.group(2) * int(match.group(1))
    def repl_empt(match):
	n = int(match.group(1))
	pat = '<table:table-cell/>'
	return pat*n if (n<100) else pat

    p_repl = re.compile(r'<table:table-cell [^>]*?repeated="(\d+)[^/>]*>(.+?table-cell>)')
    p_empt = re.compile(r'<table:table-cell [^>]*?repeated="(\d+)[^>]*>')
    xml = re.sub(p_repl, rep_repl, xml)
    xml = re.sub(p_empt, repl_empt, xml)

    d = pq(xml, parser='xml')
    ns={'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0'}
    selr = CSSSelector('table|table-row', namespaces=ns)
    selc = CSSSelector('table|table-cell', namespaces=ns)
    rowxs = pq(selr(d[0]))
    data = []
    for ir,rowx in enumerate(rowxs):
	cells = pq(selc(rowx))
	if cells.text():
	    data.append([cells.eq(ic).text().encode('utf-8') for ic in range(len(cells))])

    root,ext=os.path.splitext(filepath)
    with open(''.join([root,'.csv']),'wb') as f:
	for row in data:
	    dw = csv.writer(f)
	    dw.writerow(row)


drive_service = authenticateUser()

print 'Searching for the spreadsheet'
brandMetaData = lookForFile(drive_service, BrandrethSpreadsheetName)

print 'Downloading the spreadsheet'
resp, content = drive_service._http.request(brandMetaData['exportLinks']['application/x-vnd.oasis.opendocument.spreadsheet'])
f = open('temp.xlsx', 'w')
f.write(content)
f.close()

ods2csv('temp.xlsx')
os.remove('temp.xlsx')
print 'Done'
