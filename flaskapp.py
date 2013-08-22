import csv
import re
import datetime
from flask import Flask
from operator import itemgetter
app = Flask(__name__, static_folder='static', static_url_path='')

def urlify(name):
	nameUrl = name.lower()
	nameUrl = re.sub(r'\W', '_', nameUrl)
	return nameUrl

def escapeEntry(entry):
	entry = entry.replace('&', '&amp;')
	entry = entry.replace('<', '&lt;')
	entry = entry.replace('>', '&gt;')
	return entry

def sortTripIndicesByDate(tripsDict, descending=False):
	tripDates = {}
	for tripIndex in tripsDict.keys():
		tripDates[tripsDict[tripIndex]['data']['startDate']] = tripIndex
	tripDatesList = tripDates.keys()
	tripDatesList.sort(reverse=descending)
	returnList = []
	for date in tripDatesList:
		returnList.append(tripDates[date])
	return returnList

def formatDate(date):
	return str(date.month) + "/" + str(date.day) + "/" + str(date.year)

def calculateVisitorDuration(name, tripsDict):
	name = urlify(name)
	duration = 0
	for tripIndex in tripsdict.keys():
		for personAndIndex in tripsDict[tripIndex].keys():
			if personAndIndex != 'data':
				person = personAndIndex.split('|')[0]
	return

def buildTripsDict():
	tripsDict = {}
	with open('temp.csv', 'r') as csvfile:
		reader = csv.reader(csvfile)
		firstRow = True
		entryIndexCounter = 0
		tripIndexCounter = 0
		for row in reader:
			if not firstRow:
				startDateOfTrip = row[2]
				endDateOfTrip = row[3]
				startDateTokens = startDateOfTrip.split('/')
				endDateTokens = endDateOfTrip.split('/')
				if len(startDateTokens) is 3 and len(endDateTokens) is 3:
					source = row[5]
					reason = row[6]

					startDateOfTrip = datetime.date(int(startDateTokens[2]), int(startDateTokens[0]), int(startDateTokens[1]))
					endDateOfTrip = datetime.date(int(endDateTokens[2]), int(endDateTokens[0]), int(endDateTokens[1]))
					matchingTrip = None
					for tripIndex in tripsDict.keys():
						if tripsDict[tripIndex]['data']['startDate'] <= endDateOfTrip and tripsDict[tripIndex]['data']['startDate'] >= startDateOfTrip:
							matchingTrip = tripIndex
						if tripsDict[tripIndex]['data']['endDate'] <= endDateOfTrip and tripsDict[tripIndex]['data']['endDate'] >= startDateOfTrip:
							matchingTrip = tripIndex


					if matchingTrip != None:
						for tripIndex in tripsDict.keys():
							if tripIndex == matchingTrip:
								outingDict = tripsDict[tripIndex]
					else:
						tripsDict[tripIndexCounter] = {}
						tripsDict[tripIndexCounter]['data'] = {'reason':reason, 'startDate':startDateOfTrip,'endDate':endDateOfTrip, 'index':-1}
						outingDict = tripsDict[tripIndexCounter]
						tripIndexCounter += 1

					nameDict = {}
					nameDict["nickname"] = row[1]
					nameDict["startDate"] = startDateOfTrip
					nameDict["endDate"] = endDateOfTrip
					
					sourceEntry = escapeEntry(row[4])
					entryTokens = sourceEntry.split('_')
					entry = ''
					openingTag = False
					firstItem = True
					for item in entryTokens:
						if not firstItem:
							if not openingTag:
								entry += '<u>'
								openingTag = True
							else:
								entry += '</u>'
								openingTag = False
						entry += item
						firstItem = False
						
					nameDict["entry"] = entry
					nameDict["source"] = source
					nameDict["index"] = entryIndexCounter

					outingDict[row[0] + '|' + str(entryIndexCounter)] = nameDict

					tripDatesChanged = False
					if outingDict['data']['startDate'] > startDateOfTrip:
						outingDict['data']['startDate'] = startDateOfTrip
						tripDatesChanged = True
						
					if outingDict['data']['endDate'] < endDateOfTrip:
						outingDict['data']['endDate'] = endDateOfTrip
						tripDatesChanged = True

					if tripDatesChanged:
						for tripIndex in tripsDict.keys():
							startDateOfTempTrip = tripsDict[tripIndex]['data']['startDate']
							endDateOfTempTrip = tripsDict[tripIndex]['data']['endDate']
							startDateOfThisTrip = outingDict['data']['startDate']
							endDateOfThisTrip = outingDict['data']['endDate']
							if startDateOfThisTrip < startDateOfTempTrip and startDateOfTempTrip < endDateOfThisTrip:
								for person in tripsDict[tripIndex].keys():
									outingDict[person] = tripsDict[tripIndex][person]
								if endDateOfTempTrip > endDateOfThisTrip:
									outingDict['data']['endDate'] = endDateOfTempTrip
								del tripsDict[tripIndex]
							if startDateOfThisTrip < endDateOfTempTrip and endDateOfTempTrip < endDateOfThisTrip:
								for person in tripsDict[tripIndex].keys():
									outingDict[person] = tripsDict[tripIndex][person]
								if startDateOfTempTrip < startDateOfThisTrip:
									outingDict['data']['startDate'] = startDateOfTempTrip
								del tripsDict[tripIndex]

					entryIndexCounter += 1
			else:
				firstRow = False
	return tripsDict

@app.route('/')
def index():
	f = open('index.html')
	page = f.read()
	f.close()
	return page

@app.route('/leaderboard')
def leaderboard():
	f = open('leaderboard.html')
	page = f.read()
	f.close()
	dataset = '[["Name", "Trips"]'

	peopleDict = {}
	sources = {}
	sourceHtml = ""
	tripsDict = buildTripsDict()
	for tripIndex in tripsDict.keys():
		for person in tripsDict[tripIndex].keys():
			name = person.split('|')[0]
			if person != 'data':
				peopleDict[name] = peopleDict.get(name, 0) + 1
				source = tripsDict[tripIndex][person]["source"]
				if source not in sources.keys():
					sources[source] = []
				if person not in sources[source]:
					sources[source].append(name)
	peopleList = peopleDict.items()
	peopleList.sort(key = lambda tup: tup[1], reverse=True)

	for source in sources.keys():
		if len(sources[source]) <= 1 or source == '':
			del sources[source]
	
	sourcesList = sources.items()
	sourcesList.sort(key = lambda tup: tup[0], reverse=False)

	counter = 1
	for name in peopleList:
		dataset += ', ["' + str(counter) + ': ' + name[0].split('|')[0] + '", ' + str(name[1]) + ']'
		counter += 1
	dataset += ']'

	for source in sourcesList:
		if source[1] > 1:
			sourceHtml += '<option>' + source[0] + '</option>'

	page = page.replace('DATASET1', dataset)
	page = page.replace('SOURCE', sourceHtml)
	page = page.replace('GRAPH_HEIGHT', str(len(peopleList) * 40))
	return page

@app.route('/leaderboard/<sourceFilter>')
def leaderboardFilter(sourceFilter):
	f = open('leaderboard.html')
	page = f.read()
	f.close()
	dataset = '[["Name", "Trips"]'

	peopleDict = {}
	sources = {}
	sourceHtml = ""
	tripsDict = buildTripsDict()

	if sourceFilter == 'any':
		return leaderboard()

	for tripIndex in tripsDict.keys():
		for person in tripsDict[tripIndex].keys():
			if person != 'data':
				source = tripsDict[tripIndex][person]["source"]
				if source not in sources.keys():
					sources[source] = []
				if person not in sources[source]:
					sources[source].append(person)
				if urlify(tripsDict[tripIndex][person]["source"]) != sourceFilter:
					del tripsDict[tripIndex][person]

	for tripIndex in tripsDict.keys():
		for person in tripsDict[tripIndex].keys():
			name = person.split('|')[0]
			if name != 'data':
				peopleDict[name] = peopleDict.get(name, 0) + 1
	peopleList = peopleDict.items()
	peopleList.sort(key = lambda tup: tup[1], reverse=True)

	for source in sources.keys():
		if len(sources[source]) <= 1 or source == '':
			del sources[source]
	
	sourcesList = sources.items()
	sourcesList.sort(key = lambda tup: tup[0], reverse=False)

	counter = 1
	for name in peopleList:
		dataset += ', ["' + str(counter) + ': ' + name[0].split('|')[0] + '", ' + str(name[1]) + ']'
		counter += 1
	dataset += ']'

	for source in sourcesList:
		if source[1] > 1:
			sourceHtml += '<option>' + source[0] + '</option>'

	page = page.replace('DATASET1', dataset)
	page = page.replace('SOURCE', sourceHtml)
	page = page.replace('GRAPH_HEIGHT', str(len(peopleList) * 40))
	return page

@app.route('/stats')
def stats():
	f = open('stats.html')
	page = f.read()
	f.close()
	dataset1 = '[["Season", "Visitors"]'
	dataset2 = '['
	dataset3 = '[["Source", "Visitors"]'
	dataset4 = '[["Reason", "Trips"]'

	tripsDict1 = buildTripsDict()
	yearDict = {}
	for tripIndex in tripsDict1.keys():
		year = tripsDict1[tripIndex]['data']['startDate'].year
		if year not in yearDict.keys():
			yearDict[year] = []
		for person in tripsDict1[tripIndex].keys():
			if person != 'data' and person not in yearDict[year]:
				yearDict[year].append(person)
	yearList = []
	for year in yearDict.keys():
		yearList.append( [ year, len(yearDict[year]) ] )
	
	yearList.sort(key=lambda tup: tup[0])
	for year in yearList:
		dataset1 += ', ["' + str(year[0]) + '", ' + str(year[1]) + ']'

	dataset1 += ']'
	page = page.replace('DATASET1', dataset1)

	tripsDict3 = buildTripsDict()
	sourceDict = {}
	for tripIndex in tripsDict3.keys():
		for person in tripsDict3[tripIndex].keys():
			name = person.split('|')[0]
			if person != 'data':
				source = tripsDict3[tripIndex][person]["source"]
				if source not in sourceDict.keys():
					sourceDict[source] = []
				if name not in sourceDict[source]:
					sourceDict[source].append(name)
	sourceList = []
	for source in sourceDict.keys():
		sourceList.append( [ source, len(sourceDict[source]) ] )
	
	sourceList.sort(key=lambda tup: tup[1], reverse=True)
	for source in sourceList:
		dataset3 += ', ["' + source[0] + '", ' + str(source[1]) + ']'

	dataset3 += ']'
	page = page.replace('DATASET3', dataset3)

	tripsDict4 = buildTripsDict()
	reasonDict = {}
	for tripIndex in tripsDict4.keys():
		reason = tripsDict4[tripIndex]['data']['reason']
		reasonDict[reason] = reasonDict.get(reason, 0) + 1
	reasonList = reasonDict.items()
	
	reasonList.sort(key=lambda tup: tup[1], reverse=True)
	for reason in reasonList:
		dataset4 += ', ["' + reason[0] + '", ' + str(reason[1]) + ']'

	dataset4 += ']'
	page = page.replace('DATASET4', dataset4)

	return page

def generateTripsHtml(page, tripsDict, shouldBeReversed):
	referenceTripsDict = buildTripsDict()
	html = ""
	eventsHtml = ""
	yearsHtml = ""
	yearList = []
	for tripIndex in sortTripIndicesByDate(referenceTripsDict, True):
		if referenceTripsDict[tripIndex]['data']['startDate'].year not in yearList:
			yearList.append(referenceTripsDict[tripIndex]['data']['startDate'].year)
			yearsHtml += '<option>' + str(referenceTripsDict[tripIndex]['data']['startDate'].year) + '</option>'

		reason = referenceTripsDict[tripIndex]['data']['reason']
		if reason is not '' and not reason in eventsHtml:
				eventsHtml += '<option>' + reason + '</option>'

	for tripIndex in sortTripIndicesByDate(tripsDict, shouldBeReversed):
		startDate = formatDate(tripsDict[tripIndex]['data']['startDate'])
		endDate = formatDate(tripsDict[tripIndex]['data']['endDate'])
		reason = tripsDict[tripIndex]['data']['reason']
		numVisitors = len(tripsDict[tripIndex].keys()) - 1
		if reason is not '':
			reason = ' - ' + reason 

		if html is not "":
			html += '<ul class="nav nav-list"><li class="divider"></li></ul>'
		html += '<a href=/trips/' + str(tripIndex) + '><h3>' + startDate + ' to ' + endDate + reason + '</h3><h4>' + str(numVisitors) + ' visitors</h4></a>'

	page = page.replace('TRIPS', html)
	page = page.replace('YEARS', yearsHtml)
	page = page.replace('EVENTS', eventsHtml)
	return page


@app.route('/trips')
def trips():
	f = open('trips.html')
	page = f.read()
	f.close()

	return generateTripsHtml(page, buildTripsDict(), True)

@app.route('/trips/filter/<parameters>')
def tripsWithFilter(parameters):
	f = open('trips.html')
	page = f.read()
	f.close()

	tripsDict = buildTripsDict()

	parameterTokens = parameters.split(',')
	event = parameterTokens[0]
	del parameterTokens[0]
	year = parameterTokens[0]
	del parameterTokens[0]
	season = parameterTokens[0]
	del parameterTokens[0]
	order = parameterTokens[0]
	del parameterTokens[0]
	people = parameterTokens[0]

	#filter by events
	if event != 'any':
		for tripIndex in tripsDict.keys():
			event2 = tripsDict[tripIndex]['data']['reason']
			event2 = urlify(event2)
			if event2 != event:
				del tripsDict[tripIndex]

	#filter by year
	if year != 'any':
		for tripIndex in tripsDict.keys():
			yearNum = int(year)
			if tripsDict[tripIndex]['data']['startDate'].year != yearNum:
				del tripsDict[tripIndex]

	#filter by season
	if season != 'any':
		startMonth = 0
		startDay = 0
		endMonth = 0
		endDay = 0

		#dates of the equinoxes and solstices
		if season == 'spring':
			startMonth = 3
			startDay = 20
			endMonth = 6
			endDay = 21
		if season == 'summer':
			startMonth = 6
			startDay = 21
			endMonth = 9
			endDay = 22
		if season == 'fall':
			startMonth = 9
			startDay = 22
			endMonth = 12
			endDay = 21
		if season == 'winter':
			startMonth = 12
			startDay = 21
			endMonth = 3
			endDay = 20

		for tripIndex in tripsDict.keys():
			tripDate = tripsDict[tripIndex]['data']['startDate']
			if season != 'winter':
				if tripDate.month < startMonth or tripDate.month > endMonth:
					del tripsDict[tripIndex]
				elif tripDate.month == startMonth and tripDate.day < startDay:
					del tripsDict[tripIndex]
				elif tripDate.month == endMonth and tripDate.day > startDay:
					del tripsDict[tripIndex]
			if season == 'winter':
				if tripDate.month < startMonth and tripDate.month > endMonth:
					del tripsDict[tripIndex]
				elif tripDate.month == startMonth and tripDate.day < startDay:
					del tripsDict[tripIndex]
				elif tripDate.month == endMonth and tripDate.day > startDay:
					del tripsDict[tripIndex]

	descendingSort = True
	if order == '1':
		descendingSort = False
	
	if people != '':
		peopleTokens = people.split('_')
		for tripIndex in tripsDict.keys():
			foundThem = False
			for person in tripsDict[tripIndex].keys():
				for token in peopleTokens:
					if token in person.lower():
						foundThem = True
					if 'nickname' in tripsDict[tripIndex][person].keys() and token in tripsDict[tripIndex][person]['nickname'].lower():
						foundThem = True
			if not foundThem:
				del tripsDict[tripIndex]

	
	return generateTripsHtml(page, tripsDict, descendingSort)
			
@app.route('/trips/<int:tripIndex>')
def trip(tripIndex):
	f = open('trip.html')
	page = f.read()
	f.close()


	tripsDict = buildTripsDict()
	reason = tripsDict[tripIndex]['data']['reason']
	startDate = tripsDict[tripIndex]['data']['startDate']
	endDate = tripsDict[tripIndex]['data']['endDate']
	del tripsDict[tripIndex]['data']
	peopleList = tripsDict[tripIndex].items()
	peopleList = sorted(peopleList, key=lambda tup: tup[1]['index'])
	if reason != '':
		reason = reason + ' - '
	visitorText = ' visitors'
	if len(peopleList) == 1:
		visitorText = ' visitor'
	dateHtml = '<h1>' + formatDate(startDate) + ' to ' + formatDate(endDate) + '</h1><h2>' + reason + str(len(peopleList)) + visitorText + '</h2>'

	entriesHtml = ''

	for item in peopleList:
		print str(item) + "\n"
		person = item[0]
		personStartDate = item[1]['startDate']
		personEndDate = item[1]['endDate']
		if entriesHtml != '':
			entriesHtml += '<ul class="nav nav-list"><li class="divider"></li></ul>'
		nickname = ''
		if 'nickname' in item[1].keys() and item[1]['nickname'] != '':
			nickname = ' - ' + item[1]['nickname']
		entriesHtml += '<h3><a href=/visitors/' + urlify(person.split('|')[0]) + '>' + person.split('|')[0] + nickname + '</a></h3>'
		entriesHtml += '<h4>' + formatDate(personStartDate) + ' to ' + formatDate(personEndDate) + '</h4>'
		entriesHtml += '<p>' + item[1]['entry'] + '<p>'

	page = page.replace('DATEANDREASON', dateHtml)
	page = page.replace('ENTRIES', entriesHtml)


	return page
	
@app.route('/visitors')
def visitors():
	f = open('visitors.html')
	page = f.read()
	f.close()

	column1 = ''
	column2 = ''
	column3 = ''
	column4 = ''

	tripsDict = buildTripsDict()
	people = []
	for tripIndex in tripsDict.keys():
		for person in tripsDict[tripIndex].keys():
			name = person.split('|')[0]
			if "nickname" in tripsDict[tripIndex][person].keys() and tripsDict[tripIndex][person]['nickname'] != '':
				name += ' - ' + tripsDict[tripIndex][person]["nickname"]
			name  += '|' + person.split('|')[0]
			if not name in people:
				people.append(name)
	people.sort()
	
	counter = 0
	numPeople = len(people)
	visitors1 = ''
	visitors2 = ''
	visitors3 = ''
	visitors4 = ''
	for person in people:
		personTokens = person.split('|')
		personUrl = urlify(personTokens[1])
		if counter <= numPeople / 4:
			visitors1 += '<p><b><a href=/visitors/' + personUrl + '>' + personTokens[0] + '</a></b></p>'
		elif counter <= numPeople / 2:
			visitors2 += '<p><b><a href=/visitors/' + personUrl + '>' + personTokens[0] + '</a></b></p>'
		elif counter <= numPeople * 3 / 4:
			visitors3 += '<p><b><a href=/visitors/' + personUrl + '>' + personTokens[0] + '</a></b></p>'
		else:
			visitors4 += '<p><b><a href=/visitors/' + personUrl + '>' + personTokens[0] + '</a></b></p>'
		counter += 1

	page = page.replace('VISITORS1', visitors1)
	page = page.replace('VISITORS2', visitors2)
	page = page.replace('VISITORS3', visitors3)
	page = page.replace('VISITORS4', visitors4)

	return page

@app.route('/visitors/<name>')
def personalPage(name):
	f = open('visitor.html')
	page = f.read()
	f.close()

	nameHtml = ''
	tripsHtml = ''

	tripsDict = buildTripsDict()
	sourceTripsList = tripsDict.items()
	sourceTripsList = sorted(sourceTripsList, key=lambda tup: tup[1]['data']['startDate'], reverse=True)
	tripsList = []
	for tripTuple in sourceTripsList:
		tripIndex = tripTuple[0]
		for personAndIndex in tripsDict[tripIndex].keys():
			person = personAndIndex.split('|')[0]
			if urlify(person) == name:
				if nameHtml == '':
					nickname = ''
					if 'nickname' in tripsDict[tripIndex][personAndIndex].keys() and tripsDict[tripIndex][personAndIndex]['nickname'] != '':
						nickname = ' - ' + tripsDict[tripIndex][personAndIndex]['nickname']
					nameHtml = '<h1>' + person + nickname + '</h1>'

				if 'reason' in tripsDict[tripIndex]['data'].keys() and tripsDict[tripIndex]['data']['reason'] is not '':
					reason = ' - ' + tripsDict[tripIndex]['data']['reason']

				if tripsHtml is not '':
					tripsHtml += '<ul class="nav nav-list"><li class="divider"></li></ul>'

				tripsHtml += '<h3><a href=/trips/' + str(tripIndex) + '>' + formatDate(tripsDict[tripIndex][personAndIndex]['startDate']) + ' to ' + formatDate(tripsDict[tripIndex][personAndIndex]['endDate']) + reason + '</a></h3>'
				tripsHtml += '<p>' + tripsDict[tripIndex][personAndIndex]['entry'] + '</p>'
	
	page = page.replace('NAME', nameHtml)
	page = page.replace('ENTRIES', tripsHtml)
	
	return page

@app.route('/search')
def searchPage():
	f = open('search.html')
	page = f.read()
	f.close()

	page = page.replace('RESULTS', '')

	return page

@app.route('/search/<parameters>')
def searchWithParams(parameters):
	f = open('search.html')
	page = f.read()
	f.close()

	tripsDict = buildTripsDict()
	parameterTokens = parameters.split(',')
	descending = True
	if parameterTokens[1] == '1':
		descending = False

	searchHtml = ''

	if parameterTokens[0] != '':
		searchTokens = parameterTokens[0].split('_')
		for tripIndex in tripsDict.keys():
			for person in tripsDict[tripIndex].keys():
				if person != 'data':
					foundThem = False
					for token in searchTokens:
						if token in person.lower():
							foundThem = True
						if 'nickname' in tripsDict[tripIndex][person].keys() and token in tripsDict[tripIndex][person]['nickname'].lower():
							foundThem = True
						if token in tripsDict[tripIndex][person]['entry']:
							foundThem = True
					if foundThem == False:
						del tripsDict[tripIndex][person]
			if len(tripsDict[tripIndex].keys()) == 1:
				del tripsDict[tripIndex]
	
	sourceTripsList = tripsDict.items()
	sourceTripsList = sorted(sourceTripsList, key=lambda tup: tup[1]['data']['startDate'], reverse=True)
	for tripTuple in sourceTripsList:
		tripIndex = tripTuple[0]
		peopleList = tripTuple[1].items()
		peopleList = sorted(peopleList, key=lambda tup: tup[1]['index'])

		reason = tripTuple[1]['data']['reason']
		if reason != '':
			reason = ' - ' + reason
		startDate = tripsDict[tripIndex]['data']['startDate']
		endDate = tripsDict[tripIndex]['data']['endDate']
		searchHtml += '<h2><a href=/trips/' + str(tripIndex) + '>' + formatDate(startDate) + ' to ' + formatDate(endDate) + reason + '</a></h2>'
		entriesHtml = ''
		for personTuple in peopleList:
			person = personTuple[0]
			if person != 'data':
				if entriesHtml != '':
					entriesHtml += '<ul class="nav nav-list"><li class="divider"></li></ul>'
				nickname = ''
				if 'nickname' in tripsDict[tripIndex][person].keys() and tripsDict[tripIndex][person]['nickname'] != '':
					nickname = ' - ' + tripsDict[tripIndex][person]['nickname']
				entriesHtml += '<h4><a href=/visitors/' + urlify(person.split('|')[0]) + '>' + person.split('|')[0] + nickname + '</a></h4>'
				entriesHtml += '<p>' + tripsDict[tripIndex][person]['entry'] + '</p>'
		searchHtml += entriesHtml
	
	page = page.replace('RESULTS', searchHtml)

	return page


if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True)
