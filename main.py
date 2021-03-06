#!/usr/bin/env python
# -*- coding: utf-8 -*-

# twisted imports
from twisted.internet import defer, endpoints, protocol, reactor, task
from twisted.python import log
from twisted.words.protocols import irc

# system imports
import time, sys

# other iports
import requests
import re, json
from lxml import html
import dictionary
import random

import Calculator
import CurrencyConverter


class MessageLogger:
	"""
	An independent logger class (because separation of application
	and protocol logic is a good thing).
	"""
	def __init__(self, file):
		self.file = file

	def log(self, message):
		"""Write a message to the file."""
		timestamp = time.strftime("[%H:%M:%S]", time.localtime(time.time()))
		self.file.write('%s %s\n' % (timestamp, message))
		self.file.flush()

	def close(self):
		self.file.close()


class LogBot(irc.IRCClient):
	"""A logging IRC bot."""

	nickname = "[devbakobot]"

	def connectionMade(self):
		irc.IRCClient.connectionMade(self)
		self.logger = MessageLogger(open(self.factory.filename, "a"))
		self.logger.log("[connected at %s]" %
						time.asctime(time.localtime(time.time())))

	def connectionLost(self, reason):
		irc.IRCClient.connectionLost(self, reason)
		self.logger.log("[disconnected at %s]" %
						time.asctime(time.localtime(time.time())))
		self.logger.close()


	# callbacks for events

	def signedOn(self):
		"""Called when bot has succesfully signed on to server."""
		self.join(self.factory.channel)

	def joined(self, channel):
		"""This will get called when the bot joins the channel."""
		self.logger.log("[I have joined %s]" % channel)

	def privmsg(self, user, channel, msg):
		"""This will get called when the bot receives a message."""
		user = user.split('!', 1)[0]
		self.logger.log("<%s> %s" % (user, msg))

		# Check to see if they're sending me a private message
		if channel == self.nickname:
			reply = "It isn't nice to whisper!  Play nice with the group."
			self.msg(user, reply)
			return

		reply = u''
		if False:
			pass

		# Use dictionary
		elif msg.startswith(u"!사전"):
			url = 'https://glosbe.com/gapi/translate'
			phrase = msg.split(' ')[1]
			if len(phrase) == 0:
				reply = u"%s: 단어를 입력해주세요. (사용법 : !사전 [단어])" % (user)
			else :
				phraes = phrase.lower()
				iseng = True
				for c in phrase:
					if c not in 'qwertyuiopasdfghjklzxcvnm':
						iseng = False
						break
				params = { 'format': 'json', 'phrase': phrase }
				params['from'] = ('kor','eng')[iseng]
				params['dest'] = ('kor','eng')[1-iseng]
				res = requests.get(url, params = params)
				j = json.loads(res.content)
				meanings = ', '.join(map(lambda x: x['text'], filter(lambda x: x, map(lambda x: x.get('phrase'), j['tuc']))))
				if j['result'] != 'ok' or len(meanings) == 0:
					reply = u"%s: 찾을 수 없는 단어입니다: %s" % (user, phrase)
				else :
					reply = u"%s: %s" % (user, meanings)
			if len(reply) > 512:
				reply = reply[:509] + "..."

		elif CurrencyConverter.validate(msg):
			amount, fr, to = msg.split(' ')
			amount = int(amount)
			fr = fr.upper()
			to = to.upper()
			reply = '{} {}'.format(CurrencyConverter.convert(amount, fr, to), to)

		# Square number
		elif Calculator.validate(msg):
			reply = str(Calculator.evaluate(msg))

		# 삼겹살!
		elif (u"밥" in msg or u"저녁" in msg or u"점심" in msg) and u"뭐" in msg and u"먹" in msg:
			Bobs = [u"삼겹살", u"치킨", u"스시", u"밥"]
			reply = u"%s: %s" % (user, random.choice(Bobs))

		# Preview BOJ
		elif u"acmicpc.net/problem" in msg:
			url = 'https://www.' + re.search('acmicpc.net/problem/[0-9]+', msg).group(0)
			page = requests.get(url)
			tree = html.fromstring(page.content)
			title = ''.join([chr(ord(c)) for c in tree.xpath('//span[@id="problem_title"]/text()')[0]])
			desc = ''.join([chr(ord(c)) for c in ''.join(tree.xpath('//div[@id="problem_description"]/p/text()'))])
			reply = title + " : " + desc
			if len(reply) > 512:
				reply = reply[:509] + "..."

		# 가챠
		elif u"가챠" in msg and u"후레" not in msg and user.lower() == 'shimika':
			reply = u"%s : 175만원" % (user)

		elif msg.startswith(u"!가챠"):
			reply = u"%s : http://d.uu.gl/d/pd5rbsemky.png" % (user)

		# 단어 연관
		elif msg.startswith(u"!단어 "):
			reply = u"등록되지 않은 단어입니다"
			words = dictionary.get_translations(msg.split(u' ',1)[1])
			if len(words) > 0:
				reply = u', '.join(words)

		elif msg.startswith(u"!단어추가 "):
			words = dictionary.extract_arguments(msg.split(' ',1)[1])
			reply = u"%s 단어 두 개를 입력하세요" % (user)
			if len(words) >= 2:
				x, y = words[0], words[1]
				dictionary.add_translation(x, y)
				reply = u"%s - %s 추가됨" % (x, y)

		# If I'm tagged
		elif msg.startswith(self.nickname + ":"):
			reply = u"%s: Good Luck" % user


		# Marshall reply
		if type(reply) != type(''):
			reply = reply.encode('utf-8')
		self.msg(channel, reply)
		self.logger.log("<%s> %s" % (self.nickname, reply))


	def action(self, user, channel, msg):
		"""This will get called when the bot sees someone do an action."""
		user = user.split('!', 1)[0]
		self.logger.log("* %s %s" % (user, msg))

	# irc callbacks

	def irc_NICK(self, prefix, params):
		"""Called when an IRC user changes their nickname."""
		old_nick = prefix.split('!')[0]
		new_nick = params[0]
		self.logger.log("%s is now known as %s" % (old_nick, new_nick))


	# For fun, override the method that determines how a nickname is changed on
	# collisions. The default method appends an underscore.
	def alterCollidedNick(self, nickname):
		"""
		Generate an altered version of a nickname that caused a collision in an
		effort to create an unused related name for subsequent registration.
		"""
		return nickname + '-mochi'



class LogBotFactory(protocol.ClientFactory):
	"""A factory for LogBots.

	A new protocol instance will be created each time we connect to the server.
	"""

	def __init__(self, channel, filename):
		self.channel = channel
		self.filename = filename

	def buildProtocol(self, addr):
		p = LogBot()
		p.factory = self
		return p

	def clientConnectionLost(self, connector, reason):
		"""If we get disconnected, reconnect to server."""
		connector.connect()

	def clientConnectionFailed(self, connector, reason):
		print ("connection failed:", reason)
		reactor.stop()


if __name__ == '__main__':
	# initialize logging
	log.startLogging(sys.stdout)

	# create factory protocol and application
	f = LogBotFactory(sys.argv[1], sys.argv[2])

	# connect factory to this host and port
	reactor.connectTCP("irc.ozinger.org", 6667, f)

	# initialize dictionary
	dictionary.init_translations()

	# run bot
	reactor.run()
