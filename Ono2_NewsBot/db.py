from collections import Counter
from datetime import datetime
import mysql.connector
from time import strftime


class database:

	def __init__(self):
		self.connection = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, db=DB_DB)
		self.cursor = self.connection.cursor()


	def reconnect(self):
		self.connection = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, db=DB_DB)
		self.cursor = self.connection.cursor()


	def add_query(self, row):
		self.reconnect()
		self.cursor.execute("INSERT INTO Activities VALUES (NULL, '%d', '%s', '%s', '%s');" % (row[0], row[1], row[2], row[3]))
		self.connection.commit()
		self.connection.close()


	def get_latest_news_seen_by_id(self, chat_id):
		self.reconnect()
		self.cursor.execute('SELECT bot_answer FROM `Activities` WHERE chat_id=%d AND mess="Что нового?" ORDER BY time DESC limit 1' % chat_id)
		try:
			latest_news = self.cursor.fetchall()[0][0]
		except:
			latest_news = ''
		return latest_news
		self.connection.close()


	def get_chat_stat(self, chat_id):
		self.reconnect()

		#1) all history
		self.cursor.execute('SELECT * FROM Activities WHERE chat_id=%d' % chat_id)
		rows = self.cursor.fetchall()
		messages = [query[2] for query in rows]
		counts = Counter(messages)
		result = 'Total requests:\n' + ("\n".join(['{}: {} times'.format(k,v) for k,v in sorted(counts.items())]))

		#2) history for 24 hours
		self.cursor.execute('SELECT * FROM `Activities` WHERE time > now() - interval 1 day AND chat_id=%d' % chat_id)
		rows = self.cursor.fetchall()
		messages = [query[2] for query in rows]
		counts = Counter(messages)
		result += '\n----------------------\nLast 24 hours activity:\n' + ("\n".join(['{}: {} times'.format(k,v) for k,v in sorted(counts.items())]))
		self.connection.close()

		return result


def remind(bot,job):

	INTERVAL = 60
	TIME_PASSED = 300

	db = database()
	db.cursor.execute('SELECT chat_id, max(time) as max_time from Activities WHERE mess != "" group by chat_id;')
	rows = db.cursor.fetchall()

	curr_time = datetime.now()
	for row in rows:
		datediff = curr_time - row[1]
		if datediff.days == 0:
			if (datediff.seconds >= TIME_PASSED) and (datediff.seconds < TIME_PASSED + INTERVAL):
				result = "У меня появились свежие новости! Приходи почитать!"
				bot.sendMessage(chat_id=row[0], text=result)
				db.add_query([row[0], '', result, strftime("%Y-%m-%d %H:%M:%S")])
	return(rows)