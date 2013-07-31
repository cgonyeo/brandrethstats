import csv
import re
import datetime
from flask import Flask
app = Flask(__name__, static_folder='static', static_url_path='')

def urlify(name):
	nameUrl = name.lower()
	nameUrl = re.sub(r'\W', '_', nameUrl)
	return nameUrl

#converts mm/dd/yyyy to yyyy/mm/dd
def humanDateToMyDate(humanDate):
	humanDateTokens = humanDate.split('/')
	if len(humanDateTokens) is not 3:
		return ''
	if len(humanDateTokens[0]) is 1:
		humanDateTokens[0] = '0' + humanDateTokens[0]
	if len(humanDateTokens[1]) is 1:
		humanDateTokens[1] = '0' + humanDateTokens[1]
	return humanDateTokens[2] + '/' + humanDateTokens[0] + '/' + humanDateTokens[1]

#converts mm/dd/yyyy to yyyy/mm/dd
def myDateToHumanDate(myDate):
	myDateTokens = myDate.split('/')
	if len(myDateTokens) is not 3:
		return ''
	if myDateTokens[1][0] == '0':
		myDateTokens[1] = myDateTokens[1][-1:]
	if myDateTokens[2][0] == '0':
		myDateTokens[2] = myDateTokens[2][-1:]
	return myDateTokens[1] + '/' + myDateTokens[2] + '/' + myDateTokens[0]

def buildTripsDict():
	tripsDict = {}
	with open('temp.csv', 'r') as csvfile:
		reader = csv.reader(csvfile)
		firstRow = True
		indexCounter = 0
		for row in reader:
			if not firstRow:
				dateOfTrip = row[2]
				dateTokens = dateOfTrip.split('/')
				if len(dateTokens) is 3:
					yearNum = dateTokens[2]
					if not yearNum in tripsDict.keys():
						tripsDict[yearNum] = {}
					yearDict = tripsDict[yearNum]
					source = row[5]
					reason = row[6]

					if len(dateTokens[0]) is 1:
						dateTokens[0] = '0' + dateTokens[0]
					if len(dateTokens[1]) is 1:
						dateTokens[1] = '0' + dateTokens[1]
					monthNum = dateTokens[0]
					dayNum = dateTokens[1]
					dateOfTrip = datetime.date(int(yearNum), int(monthNum), int(dayNum))
					matchingTrip = None
					for dateAndReason in tripsDict[yearNum].keys():
						tripReason = dateAndReason.split('|')[1]
						if reason == tripReason:
							for person in tripsDict[yearNum][dateAndReason].keys():
								timedelta = tripsDict[yearNum][dateAndReason][person]["date"] - dateOfTrip
								if abs(timedelta.days) <= 4:
									matchingTrip = dateAndReason


					outingKey = ''
					if matchingTrip != None:
						outingKey = matchingTrip
					else:
						outingKey = dateTokens[2] + '/' + dateTokens[0] + '/' + dateTokens[1] + '|' + row[6]

					if not outingKey in yearDict.keys():
						yearDict[outingKey] = {}
					outingDict = yearDict[outingKey]

					nameDict = {}
					if len(row[1]) > 0:
						nameDict["nickname"] = row[1]
					nameDict["date"] = dateOfTrip

					entryTokens = row[4].split('_')
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
					nameDict["index"] = indexCounter

					outingDict[row[0]] = nameDict

					indexCounter += 1
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
	for year in tripsDict.keys():
		for dateAndReason in tripsDict[year].keys():
			for person in tripsDict[year][dateAndReason].keys():
				peopleDict[person] = peopleDict.get(person, 0) + 1
				source = tripsDict[year][dateAndReason][person]["source"]
				if source not in sources.keys():
					sources[source] = []
				if person not in sources[source]:
					sources[source].append(person)
	peopleList = peopleDict.items()
	peopleList.sort(key = lambda tup: tup[1], reverse=True)

	for source in sources.keys():
		if len(sources[source]) <= 1 or source == '':
			del sources[source]
	
	sourcesList = sources.items()
	sourcesList.sort(key = lambda tup: tup[0], reverse=False)

	counter = 1
	for person in peopleList:
		dataset += ', ["' + str(counter) + ': ' + person[0] + '", ' + str(person[1]) + ']'
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

	for year in tripsDict.keys():
		for dateAndReason in tripsDict[year].keys():
			for person in tripsDict[year][dateAndReason].keys():
				source = tripsDict[year][dateAndReason][person]["source"]
				if source not in sources.keys():
					sources[source] = []
				if person not in sources[source]:
					sources[source].append(person)
				if urlify(tripsDict[year][dateAndReason][person]["source"]) != sourceFilter:
					del tripsDict[year][dateAndReason][person]

	for year in tripsDict.keys():
		for dateAndReason in tripsDict[year].keys():
			for person in tripsDict[year][dateAndReason].keys():
				peopleDict[person] = peopleDict.get(person, 0) + 1
	peopleList = peopleDict.items()
	peopleList.sort(key = lambda tup: tup[1], reverse=True)

	for source in sources.keys():
		if len(sources[source]) <= 1 or source == '':
			del sources[source]
	
	sourcesList = sources.items()
	sourcesList.sort(key = lambda tup: tup[0], reverse=False)

	counter = 1
	for person in peopleList:
		dataset += ', ["' + str(counter) + ': ' + person[0] + '", ' + str(person[1]) + ']'
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
	for year in tripsDict1.keys():
		if year not in yearDict.keys():
			yearDict[year] = []
		for dateAndReason in tripsDict1[year].keys():
			for person in tripsDict1[year][dateAndReason].keys():
				if person not in yearDict[year]:
					yearDict[year].append(person)
	yearList = []
	for year in yearDict.keys():
		yearList.append( [ year, len(yearDict[year]) ] )
	
	yearList.sort(key=lambda tup: tup[0])
	for year in yearList:
		dataset1 += ', ["' + year[0] + '", ' + str(year[1]) + ']'

	dataset1 += ']'
	page = page.replace('DATASET1', dataset1)

	dateDict = {}
	with open('temp.csv', 'r') as csvfile:
		reader = csv.reader(csvfile)
		firstRow = True
		for row in reader:
			if not firstRow:
				tripdate = row[2]
				keyvalue = humanDateToMyDate(tripdate)
				dateDict[keyvalue] = dateDict.get(keyvalue, 0) + 1
			else:
				firstRow = False
	dateList = dateDict.items()
	dateList.sort(key=lambda tup: tup[0])
	for entry in dateList:
		if dataset2 is not '[':
			dataset2 += ', '
		datetokens = entry[0].split('/')
		if len(datetokens) is 3:
			dataset2 += '[new Date(' + datetokens[0] + ', ' + datetokens[1] + ', ' + datetokens[2] + '), ' + str(entry[1]) + ', null, null]'
	dataset2 += ']'
	page = page.replace('DATASET2', dataset2)

	tripsDict3 = buildTripsDict()
	sourceDict = {}
	for year in tripsDict3.keys():
		for dateAndReason in tripsDict3[year].keys():
			for person in tripsDict3[year][dateAndReason].keys():
				source = tripsDict3[year][dateAndReason][person]["source"]
				if source not in sourceDict.keys():
					sourceDict[source] = []
				if person not in sourceDict[source]:
					sourceDict[source].append(person)
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
	for year in tripsDict4.keys():
		for dateAndReason in tripsDict4[year].keys():
			reason = dateAndReason.split('|')[1]
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
	years = tripsDict.keys()
	years.sort(reverse=shouldBeReversed)
	html = ""
	eventsHtml = ""
	yearsHtml = ""
	for year in sorted(referenceTripsDict.keys()):
		yearsHtml += '<option>' + year + '</option>'
		dates = referenceTripsDict[year].keys()
		dates.sort()
		for dateAndReason in dates:
			dateAndReasonTokens = dateAndReason.split('|')
			reason = dateAndReasonTokens[1]
			if reason is not '' and not reason in eventsHtml:
					eventsHtml += '<option>' + reason + '</option>'

	for year in years:
		dates = tripsDict[year].keys()
		dates.sort(reverse=shouldBeReversed)

		for dateAndReason in dates:
			if html is not "":
				html += '<ul class="nav nav-list"><li class="divider"></li></ul>'
			numVisitors = len(tripsDict[year][dateAndReason].keys())

			dateAndReasonTokens = dateAndReason.split('|')
			date = dateAndReasonTokens[0]
			reason = dateAndReasonTokens[1]
			urlReason = urlify(reason)
			date = myDateToHumanDate(date)
			if reason is not '':
				reason = ' - ' + reason 
				urlReason = ',' + urlReason

			html += '<a href=/trips/' + urlify(date) + urlReason + '><h3>' + date + reason + '</h3><h4>' + str(numVisitors) + ' visitors</h4></a>'

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
		for year2 in tripsDict.keys():
			for dateAndReason in tripsDict[year2].keys():
				event2 = dateAndReason.split('|')[1]
				event2 = urlify(event2)
				if event2 != event:
					del tripsDict[year2][dateAndReason]

	#filter by year
	if year != 'any':
		for year3 in tripsDict.keys():
			if year3 != year:
				del tripsDict[year3]

	#filter by season
	if season != 'any':
		startMonth = '00'
		startDay = '00'
		endMonth = '00'
		endDay = '00'

		#dates of the equinoxes and solstices
		if season == 'spring':
			startMonth = '03'
			startDay = '20'
			endMonth = '06'
			endDay = '21'
		if season == 'summer':
			startMonth = '06'
			startDay = '21'
			endMonth = '09'
			endDay = '22'
		if season == 'fall':
			startMonth = '09'
			startDay = '22'
			endMonth = '12'
			endDay = '21'
		if season == 'winter':
			startMonth = '12'
			startDay = '21'
			endMonth = '03'
			endDay = '20'

		for year4 in tripsDict.keys():
			for dateAndReason in tripsDict[year4].keys():
				dateTokens = dateAndReason.split('|')[0].split('/') #<--this just looks like a bad idea...
				if season != 'winter':
					if int(dateTokens[1]) < int(startMonth) or int(dateTokens[1]) > int(endMonth):
						del tripsDict[year4][dateAndReason]
					elif int(dateTokens[1]) == int(startMonth) and int(dateTokens[2]) < int(startDay):
						del tripsDict[year4][dateAndReason]
					elif int(dateTokens[1]) == int(endMonth) and int(dateTokens[2]) > int(startDay):
						del tripsDict[year4][dateAndReason]
				if season == 'winter':
					if int(dateTokens[1]) < int(startMonth) and int(dateTokens[1]) > int(endMonth):
						del tripsDict[year4][dateAndReason]
					elif int(dateTokens[1]) == int(startMonth) and int(dateTokens[2]) < int(startDay):
						del tripsDict[year4][dateAndReason]
					elif int(dateTokens[1]) == int(endMonth) and int(dateTokens[2]) > int(startDay):
						del tripsDict[year4][dateAndReason]

	descendingSort = True
	if order == '1':
		descendingSort = False
	
	if people != '':
		peopleTokens = people.split('_')
		for year5 in tripsDict.keys():
			for dateAndReason in tripsDict[year5].keys():
				foundThem = False
				for person in tripsDict[year5][dateAndReason].keys():
					for token in peopleTokens:
						if token in person.lower():
							foundThem = True
						if 'nickname' in tripsDict[year5][dateAndReason][person].keys() and token in tripsDict[year5][dateAndReason][person]['nickname'].lower():
							foundThem = True
				if not foundThem:
					del tripsDict[year5][dateAndReason]

	
	return generateTripsHtml(page, tripsDict, descendingSort)
			
@app.route('/trips/<date>')
def trip(date):
	f = open('trip.html')
	page = f.read()
	f.close()

	tripReason = ''
	if ',' in date:
		dateTokens = date.split(',')
		date = dateTokens[0]
		tripReason = dateTokens[1]

	tripsDict = buildTripsDict()
	dateAndReason = ''
	dateAndReasonDict = {}
	date = humanDateToMyDate(date.replace('_','/'))
	
	year = tripsDict[date[:4]]
	for item in sorted(year.keys()):
		itemTokens = item.split('|')
		itemDate = itemTokens[0]
		itemReason = itemTokens[1]
		if date == itemDate and tripReason == urlify(itemReason):
			dateAndReason = item
			dateAndReasonDict = year[item]
	
	reason = dateAndReason.split('|')[1]
	if reason != '':
		reason = ' - ' + reason
	dateHtml = '<h1>' + myDateToHumanDate(date) + reason + '<h1>'
	entriesHtml = ''

	peopleList = dateAndReasonDict.items()
	peopleList.sort(key=lambda tup: tup[1]["index"])

	print peopleList

	for item in peopleList:
		person = item[0]
		date = dateAndReasonDict[person]["date"]
		if entriesHtml != '':
			entriesHtml += '<ul class="nav nav-list"><li class="divider"></li></ul>'
		nickname = ''
		if 'nickname' in dateAndReasonDict[person].keys():
			nickname = ' - ' + dateAndReasonDict[person]['nickname']
		entriesHtml += '<h3><a href=/visitors/' + urlify(person) + '>' + person + nickname + '</a></h3>'
		entriesHtml += '<h4>' + str(date.month) + '/' + str(date.day) + '/' + str(date.year) + '</h4>'
		entriesHtml += '<p>' + dateAndReasonDict[person]['entry'] + '<p>'

	#for person in sorted(dateAndReasonDict.keys()):
	#	date = dateAndReasonDict[person]["date"]
	#	if entriesHtml != '':
	#		entriesHtml += '<ul class="nav nav-list"><li class="divider"></li></ul>'
	#	nickname = ''
	#	if 'nickname' in dateAndReasonDict[person].keys():
	#		nickname = ' - ' + dateAndReasonDict[person]['nickname']
	#	entriesHtml += '<h3><a href=/visitors/' + urlify(person) + '>' + person + nickname + '</a></h3>'
	#	entriesHtml += '<h4>' + str(date.month) + '/' + str(date.day) + '/' + str(date.year) + '</h4>'
	#	entriesHtml += '<p>' + dateAndReasonDict[person]['entry'] + '<p>'
	
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
	for year in tripsDict.keys():
		for dateAndReason in tripsDict[year].keys():
			for person in tripsDict[year][dateAndReason].keys():
				if not person in people:
					people.append(person)
	people.sort()
	
	counter = 0
	numPeople = len(people)
	visitors1 = ''
	visitors2 = ''
	visitors3 = ''
	visitors4 = ''
	for person in people:
		personUrl = urlify(person)
		if counter <= numPeople / 4:
			visitors1 += '<p><b><a href=/visitors/' + personUrl + '>' + person + '</a></b></p>'
		elif counter <= numPeople / 2:
			visitors2 += '<p><b><a href=/visitors/' + personUrl + '>' + person + '</a></b></p>'
		elif counter <= numPeople * 3 / 4:
			visitors3 += '<p><b><a href=/visitors/' + personUrl + '>' + person + '</a></b></p>'
		else:
			visitors4 += '<p><b><a href=/visitors/' + personUrl + '>' + person + '</a></b></p>'
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
	for year in sorted(tripsDict.keys(), reverse=True):
		for dateAndReason in sorted(tripsDict[year].keys(), reverse=True):
			for person in sorted(tripsDict[year][dateAndReason].keys(), reverse=True):
				if urlify(person) == name:
					if nameHtml == '':
						nickname = ''
						if 'nickname' in tripsDict[year][dateAndReason][person].keys():
							nickname = ' - ' + tripsDict[year][dateAndReason][person]['nickname']
						nameHtml = '<h1>' + person + nickname + '</h1>'
					dateAndReasonTokens = dateAndReason.split('|')
					dateTokens = dateAndReasonTokens[0].split('/')

					if dateTokens[1][0] is '0':
						dateTokens[1] = dateTokens[1][-1:]
					if dateTokens[2][0] is '0':
						dateTokens[2] = dateTokens[2][-1:]

					reason = dateAndReasonTokens[1]
					urlReason = urlify(dateAndReasonTokens[1])

					if reason is not '':
						reason = ' - ' + reason
						urlReason = ',' + urlReason

					if tripsHtml is not '':
						tripsHtml += '<ul class="nav nav-list"><li class="divider"></li></ul>'
					tripsHtml += '<h3><a href=/trips/' + urlify(myDateToHumanDate(dateAndReasonTokens[0])) + urlReason + '>' + dateTokens[1] + '/' + dateTokens[2] + '/' + dateTokens[0] + reason + '</a></h3>'
					tripsHtml += '<p>' + tripsDict[year][dateAndReason][person]['entry'] + '</p>'
	
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
		for year in tripsDict.keys():
			for dateAndReason in sorted(tripsDict[year].keys()):
				for person in sorted(tripsDict[year][dateAndReason].keys()):
					foundThem = False
					for token in searchTokens:
						if token in person.lower():
							foundThem = True
						if 'nickname' in tripsDict[year][dateAndReason][person].keys() and token in tripsDict[year][dateAndReason][person]['nickname'].lower():
							foundThem = True
						if token in tripsDict[year][dateAndReason][person]['entry']:
							foundThem = True
					if foundThem == False:
						del tripsDict[year][dateAndReason][person]
				if len(tripsDict[year][dateAndReason].keys()) == 0:
					del tripsDict[year][dateAndReason]
	
	for year in sorted(tripsDict.keys(), reverse=descending):
		for dateAndReason in sorted(tripsDict[year].keys(), reverse=descending):
			dateAndReasonTokens = dateAndReason.split('|')
			reason = dateAndReasonTokens[1]
			urlReason = urlify(reason)
			if reason != '':
				reason = ' - ' + reason
				urlReason = ',' + urlReason
			date = myDateToHumanDate(dateAndReasonTokens[0])
			searchHtml += '<h2><a href=/trips/' + urlify(date) + urlReason + '>' + date + reason + '</a></h2>'
			entriesHtml = ''
			for person in sorted(tripsDict[year][dateAndReason].keys(), reverse=descending):
				if entriesHtml != '':
					entriesHtml += '<ul class="nav nav-list"><li class="divider"></li></ul>'
				nickname = ''
				if 'nickname' in tripsDict[year][dateAndReason][person].keys():
					nickname = ' - ' + tripsDict[year][dateAndReason][person]['nickname']
				entriesHtml += '<h4><a href=/visitors/' + urlify(person) + '>' + person + nickname + '</a></h4>'
				entriesHtml += '<p>' + tripsDict[year][dateAndReason][person]['entry'] + '</p>'
			searchHtml += entriesHtml
	
	page = page.replace('RESULTS', searchHtml)

	return page


if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True)
