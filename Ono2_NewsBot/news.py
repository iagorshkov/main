from bs4 import BeautifulSoup
import csv
import db
import mysql.connector
from nltk import FreqDist
import pymorphy2
from random import choice, sample
from string import punctuation
import urllib.request


NEWS_LOCATION = 'data/news.csv'

exclude = "[" + punctuation + "'0123456789[]—«»–]"
alt_normal_forms = {"газа":"газ", "Песков":"песков"}
cands = ['NOUN']
stopwords = ['россия', 'сша']


def normal_form(text):
	news_text = text.split()
	normal_text = []

	morph = pymorphy2.MorphAnalyzer()

	for word in news_text:
		word_cleaned = ''.join(ch for ch in word if ch not in exclude)
		if word_cleaned != '':
			if word_cleaned in alt_normal_forms.keys():
				normal_text.append(alt_normal_forms[word_cleaned])
			else:
				normal_text.append(morph.parse(word_cleaned)[0].normal_form)
	return ' '.join(normal_text)



def upd_news(bot, job):

	with open(NEWS_LOCATION, 'w') as news_file:
		csvwriter = csv.writer(news_file)

		rss_url = 'https://news.yandex.ru/index.rss'
		raw_html = urllib.request.urlopen(rss_url).read().decode('utf-8')
		soup = BeautifulSoup(raw_html, 'html.parser')
		news = soup.find_all('item')
		for item in news:

			news_title = item.title.getText()
			news_description = item.description.getText()

			csvwriter.writerows([[news_title, normal_form(news_title), item.guid.getText(),
						  news_description, normal_form(news_description)]])



def get_random_news(chat_id, use_db=False):

	news_file = open(NEWS_LOCATION, 'r')
	csvreader = list(csv.reader(news_file))[:10]
	if db:
		latest_news = db.database().get_latest_news_seen_by_id(chat_id)
		while True:
			rand_news = choice(csvreader)
			if rand_news[0] != ' '.join(latest_news.split()[:-1])[:-1]:
				break
	else:
		rand_news = choice(csvreader)
	return rand_news[0] + ': ' + rand_news[2]



#Returns corpus that contains only nouns
def preproc(corpus):
	for i, doc in enumerate(corpus):
		doc_words = doc.split()

		morph = pymorphy2.MorphAnalyzer()

		nouns = []
		for word in doc_words:
			if word not in stopwords:
				try:
					gram_info = morph.parse(word)[0]
					if 'NOUN' in gram_info.tag:
						nouns.append(word)
				except:
					pass
		corpus[i] = ' '.join(nouns)
	return corpus


def get_tags():

	with open(NEWS_LOCATION, 'r') as f:
		csvreader = csv.reader(f)
		news_list = list(csvreader)
		
	headers = [news[1] for news in news_list]
	texts = [news[4] for news in news_list]
	news = list(map(lambda x, y:x+ ' ' + y, headers, texts))
	words = ' '.join(preproc(news)).split( )
	top = FreqDist(words).most_common(8)
	top = [pair[0] for pair in top]
	rand_news = sample(top[3:],2)

	return top[:3] + rand_news

def get_news_by_tag(tag):
	with open(NEWS_LOCATION, 'r') as f:
		csvreader = csv.reader(f)
		news_list = list(csvreader)
	headers = [news[1] for news in news_list]
	texts = [news[4] for news in news_list]
	news_list_preproc = list(map(lambda x, y:x+ ' ' + y, headers, texts))

	relevant_news = []

	for i, news in enumerate(news_list_preproc):
		if tag in news:
			relevant_news.append(news_list[i][0] + ':\n\n' + news_list[i][3])

	if len(relevant_news) > 0:
		result = choice(relevant_news)
	else:
		result = 'Эта тема больше не актуальна и по ней новостей нет'
	return result