import time
from datetime import datetime

import requests

validCurrency = [
	'CAD',
	'CNY',
	'EUR',
	'GBP',
	'JPY',
	'KRW',
	'USD',
]

# i.e. exchangeCache['CAD']['KRW'] = {rate: 830.91, lastFetch: 1528860236.7085433}
exchangeCache = { }

def dumpRate(fr, to):
	if fr not in exchangeCache:
		return
	if to not in exchangeCache[fr]:
		return
	rate = exchangeCache[fr][to]['rate']
	lastFetch = exchangeCache[fr][to]['lastFetch']

	with open('rate_history.txt', 'a+') as f:
		f.write('{}: 1 {} = {} {}\n'.format(
			lastFetch,
			fr,
			rate,
			to))

def validate(msg):
	msgs = msg.split(' ')
	if len(msgs) != 3:
		return False
	amount, fr, to = msgs

	if not amount.isdigit():
		return False
	if fr.upper() not in validCurrency:
		return False
	if to.upper() not in validCurrency:
		return False
	return True

# at most once every 30 minutes
def needFetch(fr, to):
	if fr not in exchangeCache:
		return True
	if to not in exchangeCache[fr]:
		return True

	FetchInterval = 1800
	now = time.time()
	lastFetch = exchangeCache[fr][to]['lastFetch']
	return now - lastFetch > FetchInterval

def fetchRate(fr, to):
	fetchTime = 0
	rate = 0
	tries = 10
	while tries:
		try:
			host = 'http://free.currencyconverterapi.com/api/v5/convert'
			qCode = fr + '_' + to
			res = requests.get(host, params={'q': qCode}).json()
			fetchTime = time.time()
			rate = res['results'][qCode]['val']
			break
		except:
			print ("fetch failed:", params)
		tries -= 1
	return (fetchTime, rate)

def getRate(fr, to):
	if fr not in exchangeCache:
		exchangeCache[fr] = {}
	if to not in exchangeCache[fr]:
		exchangeCache[fr][to] = {'rate': 0, 'lastFetch': 0}

	fetchTime = exchangeCache[fr][to]['lastFetch']
	rate = exchangeCache[fr][to]['rate']

	if needFetch(fr, to):
		fetchTime, rate = fetchRate(fr, to)
		exchangeCache[fr][to] = {'rate': rate, 'lastFetch': fetchTime}
		dumpRate(fr, to)

	return rate

# amount : int
# fr : validCurrency
# to : validCurrency
def convert(amount, fr, to):
	rate = getRate(fr, to)
	return amount * rate
