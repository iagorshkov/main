from collections import Counter
from datetime import datetime
import psycopg2
from time import strftime
import json

with open('config.json', 'r') as file:
	text = file.read()
	DB_HOST = json.loads(text)['DB_HOST']
	DB_NAME = json.loads(text)['DB_NAME']
	DB_USER = json.loads(text)['DB_USER']
	DB_PASSWORD = json.loads(text)['DB_PASSWORD']

DB_HOST = "ec2-23-21-220-48.compute-1.amazonaws.com"
DB_NAME = "d73bdkrptlb9je"
DB_USER = "dgpbnpnqukrzzo"
DB_PASSWORD = "1be32a7d449ca8a9a2208ccaa6f48223326c9759e941a17f2b9117e8c632e701"

class database:

	def __init__(self):
		self.connection = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
		self.cursor = self.connection.cursor()


	def save_user_mess(self, row):
		self.cursor.execute("INSERT INTO user_messages (chat_id, mess, time) VALUES ('%d', '%s', '%s');" % (row[0], row[1], 
			row[2]))
		self.connection.commit()
		self.connection.close()


	def get_chat_stat(self, chat_id):

		#1) all history
		self.cursor.execute('SELECT * FROM user_messages WHERE chat_id=%d' % chat_id)
		rows = self.cursor.fetchall()
		messages = [query[2] for query in rows]
		counts = Counter(messages)
		result = 'Total requests:\n' + ("\n".join(['{}: {} times'.format(k,v) for k,v in sorted(counts.items())]))

		#2) history for 24 hours
		self.cursor.execute("SELECT * FROM user_messages WHERE time > NOW() - INTERVAL '1 day' AND chat_id=%d" % chat_id)
		rows = self.cursor.fetchall()
		messages = [query[2] for query in rows]
		counts = Counter(messages)
		result += '\n----------------------\nLast 24 hours activity:\n' + ("\n".join(['{}: {} times'.format(k,v) for k,v in sorted(counts.items())]))
		self.connection.close()

		return result


	def get_user_ids(self):
		self.cursor.execute('SELECT DISTINCT chat_id FROM user_messages;')
		return self.cursor.fetchall()


def remind(bot,job):

	INTERVAL = 120
	TIME_PASSED = 21600

	db = database()
	db.cursor.execute('SELECT chat_id, max(time) as max_time from user_messages group by chat_id;')
	rows = db.cursor.fetchall()
	curr_time = datetime.now()
	for row in rows:
		datediff = curr_time - row[1]
		if datediff.days == 0:
			if (datediff.seconds >= TIME_PASSED) and (datediff.seconds < TIME_PASSED + INTERVAL):
				result = "У меня появились свежие новости! Приходи почитать! ✌✌✌"
				bot.sendMessage(chat_id=row[0], text=result)
	return(rows)