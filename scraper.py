# -*- coding: utf-8 -*-

import sys
import re
import os
import math
from time import sleep
from datetime import datetime
import threading
from variables import *
from bs4 import BeautifulSoup, SoupStrainer
import MySQLdb
from cgi import escape
from collections import Counter

# connect
db = MySQLdb.connect(host="localhost", user="root", passwd="root", db="jvdata", unix_socket='/Applications/MAMP/tmp/mysql/mysql.sock')
anchor_list = []
connected = ""
# Main Function
def main(): 
	s = requests.Session()
	url = "http://www.jeuxvideo.com/forums/42-19163-48767439-1-0-1-0-worlds-2016-quarterfinals.htm"
	print red + url + white
	# url = "http://www.jeuxvideo.com/forums/42-19163-48757233-1-0-1-0-cherche-duo-en-mid-plat-je-main-support.htm"
	# url = "http://www.jeuxvideo.com/forums/42-19163-48747237-1-0-1-0-analyse-azir-en-ce-moment.htm"

	while 1:
		last_page = getLastPage(url, s)
		try:
			r = singleRequest(last_page, s)
			get_messages(r)
			sleep(5)
		except:
			pass


def getLastPage(url, s):
	global connected
	r = singleRequest(url, s)
	try:
		soup = BeautifulSoup(r.text, "html.parser")
		connected = soup.find('span', 'nb-connect-fofo').text.split(' ')[0]
		topics = soup.find('div', 'bloc-liste-num-page')
		last_page = '1'
		for to in topics:
			try:
				page = to.getText()
				if page != '»'.decode('utf-8'):
					last_page = page
			except:
				pass
		# Last page of the topic
		topic_lastpage = url.split('-')
		topic_lastpage[3] = last_page
		topic_lastpage = '-'.join(topic_lastpage)
		return topic_lastpage
	except:
		pass

# Parse each message
def get_messages(page):
	global connected
	global anchor_list
	bloc_message = SoupStrainer('div', {'class': 'bloc-message-forum '})
	soup = BeautifulSoup(page.text, "html.parser", parse_only=bloc_message)
	bulk_insert = []
	trends = []
	for s in soup:
		ancre_duplicate = 0
		# PSEUDO
		try:
			pseudo = s.find('span', attrs={'class': 'bloc-pseudo-msg'})
			pseudo = pseudo.getText().replace(' ', '').replace('\n', '')
		except:
			pseudo = "Pseudo supprime"
		# ANCRE
		ancre = s['data-id']

		
		# MESSAGE
		message_raw = s.find('div', attrs={'class': 'text-enrichi-forum'})
		message = message_raw.renderContents().replace('\n', '')
		message_raw = message_raw.getText()
		message_raw = ' '.join(message_raw.split())

		each_word = message_raw.split(' ')
		for word in each_word:
			trends.append(word)

		nb_mots = len(message_raw.split(' '))
		nb_chars = len(message_raw)

		# DATE
		date = s.find('div', attrs={'class': 'bloc-date-msg'}).text.replace('\n', '').replace('"', '').lstrip()
		date = parse_date(date)

		# AVATAR
		try:
			avatar = s.find('img', attrs={'class': 'user-avatar-msg'})
			avatar = avatar['data-srcset'].replace('avatar-sm', 'avatar-md').replace('//image.jeuxvideo.com/', '') # Add 'image.jeuxvideo.com' in frontend
		except:
			avatar = "image.jeuxvideo.com/avatar-md/default.jpg"	

		for anc in anchor_list:
			if ancre == anc:
				ancre_duplicate = 1
		if (ancre_duplicate == 0):
			print cyan + pseudo + ' ' + str(date).split(' ')[1] + ' ' + connected + ' connectes' + white
			print yellow + message_raw + white
			print '_________________________________'
			sys.stdout.write('\a')
			sys.stdout.flush()
			anchor_list.append(ancre)

		# red = "\033[31m";
		# green = "\033[32m";
		# magenta = "\033[35m";
		# cyan = "\033[36m";
		# blue = "\033[34m";
		# yellow = "\033[33m";
		# white = "\033[0m";

		row_list = (pseudo, ancre, message_raw, date, avatar)
		bulk_insert.append(row_list)
		# cursor.execute("""INSERT INTO messages (pseudo,ancre,message,date,avatar) VALUES (%s,%s,%s,%s,%s) """,(pseudo,ancre,message_raw,date,avatar))
	# threads = []
	# t = threading.Thread(target=bulkinsert, args=(bulk_insert,))
	# threads.append(t)
	# t.start()
	
	c=Counter(trends)
	k = c.most_common()
	ban_loop = 1
	ban = 0
	# while ban_loop == 1:
	# 	if (
	# 		k[ban][0] == "de" or
	# 		k[ban][0] == "que")
	# 		ban += 1
	# 	else:
	# 		ban_loop = 0

	# print 'Most Common Word 1: ' + yellow + k[ban][0] + white

	bulk_insert = bulk_insert[::-1]
	# print bulk_insert
	# if bulkinsert(bulk_insert) == 1:
	# 	return 1
	return 0
	
def bulkinsert(bulk_insert):
	cursor = db.cursor()
	for row in bulk_insert:
		try:
			cursor.execute("""INSERT INTO messages (pseudo,ancre,message,date,avatar) VALUES (%s,%s,%s,%s,%s) """, row)
			db.commit()
		except MySQLdb.IntegrityError:
			return 1
	return 0

def parse_date(date):
	p_date = date.split(' ')
	# Encode characters
	d = p_date[0]
	p_date[1] = p_date[1].encode('utf8', 'replace')
	if 'janvier' in p_date[1]:
		m = '01'
	elif 'février' in p_date[1]:
		m = '02'
	elif 'mars' in p_date[1]:
		m = '03'
	elif 'avril' in p_date[1]:
		m = '04'
	elif 'mai' in p_date[1]:
		m = '05'
	elif 'juin' in p_date[1]:
		m = '06'
	elif 'juillet' in p_date[1]:
		m = '07'
	elif 'août' in p_date[1]:
		m = '08'
	elif 'septembre' in p_date[1]:
		m = '09'
	elif 'octobre' in p_date[1]:
		m = '10'
	elif 'novembre' in p_date[1]:
		m = '11'
	elif 'décembre' in p_date[1]:
		m = '12'
	y = p_date[2]
	h = p_date[4].split(':')
	ladate = datetime(int(y), int(m), int(d), int(h[0]), int(h[1]), int(h[2]))
	return ladate

main()









