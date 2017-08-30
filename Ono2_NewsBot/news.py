from bs4 import BeautifulSoup
from datetime import timedelta, datetime
import db
from nltk import FreqDist
import pymorphy2
from random import choice, sample
from string import punctuation
import requests
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from random import choice
from scipy.cluster.hierarchy import fcluster, linkage
from newspaper import Article
import re
import botan
from tqdm import tqdm


NEWS_LOCATION = 'data/news.csv'

exclude = "[" + punctuation + "'0123456789[]—«»–]"
alt_normal_forms = {"газа":"газ", "Песков":"песков"}
cands = ['NOUN']
stopwords = ['россия', 'сша']


def represent_news(text):
	words = text.split()
	if len(words[0]) > 7:
		news_start = words[0]
		news_other = ' '.join(words[1:])
	else:
		news_start = ' '.join(words[:2])
		news_other = ' '.join(words[2:])
	return news_start, news_other


def normal_form(text):
	text = re.sub(r'([^\s\w])', '', text)
	news_text = text.split()
	nouns = []

	morph = pymorphy2.MorphAnalyzer()

	for word in news_text:
		word_cleaned = ''.join(ch for ch in word if ch not in exclude)
		if word_cleaned != '':
			gram_info = morph.parse(word)[0]
			if 'NOUN' in gram_info.tag or 'VERB' in gram_info.tag or 'ADJF' in gram_info.tag:
				try:
					nouns.append(morph.parse(word)[0].normal_form)
				except:
					pass
	return ' '.join(nouns)


def clean_text(text):
	return text.replace('&quot', '').replace('\n', '').replace('\xa0',' ')


def parse_rss(rss_url):
	new = []

	raw_html = requests.get(rss_url).text
	soup = BeautifulSoup(raw_html, 'html.parser')
	news = soup.find_all('item')
	for item in news:
		try:
			news_title = clean_text(item.title.getText())
			news_description = ''
			if item.description is not None:
				news_description = clean_text(item.description.getText())
			news_pubdate = ''.join(item.pubdate.getText()[:-6].split(',')[1:]).strip()
			news_link = item.link.getText()
			news_source = re.findall('/([a-z.]+).(io|com|ru)', rss_url)[0][0].split('.')[-1].capitalize()
			new.append([news_title, normal_form(news_title), news_link, 
					 news_description, normal_form(news_description), news_pubdate, news_source])
		except:
			pass
	return new


def upd_news():
	print('updating news...')

	meduza_news = parse_rss('https://meduza.io/rss/news')
	interfax_news = parse_rss('http://interfax.ru/rss.asp')
	lenta_news = parse_rss('https://lenta.ru/rss')
	tass_news = parse_rss('http://tass.ru/rss/v2.xml')
	rambler_news = parse_rss('https://news.rambler.ru/rss/head/')
	russia_today_news = parse_rss('https://russian.rt.com/rss')
	vedomosti_news = parse_rss('https://vedomosti.ru/rss/news')
	total_news = tass_news + vedomosti_news + lenta_news + meduza_news + interfax_news + rambler_news + russia_today_news

	database = db.database()
	database.cursor.execute('select link from news;')
	links = database.cursor.fetchall()
	links = [link[0] for link in links]
	new_news = []
	for c, news in tqdm(enumerate(total_news)):
		if datetime.now() - datetime.strptime(news[5], "%d %b %Y %H:%M:%S") < timedelta(days=1):
			if not news[2] in links:
				article = Article(news[2], language='ru')
				article.download()
				try:
					article.parse()
				except:
					pass
				news.append(article.text)
				news.append(normal_form(article.text))
				news += [0,0]
				new_news.append(news)

	print('pasting in db...')
	database.connection.commit()
	database.connection.close()
	database = db.database()
	for news in tqdm(new_news):
		if not database.if_news_exists(news[2]):
			try:
				database.save_news(news)
				database.connection.commit()
			except:
				pass

	database.delete_old_news()


def get_hot_news():
	database = db.database()
	database.cursor.execute('select * from news where hot_topic>3 order by hot_topic desc;')
	hot = database.cursor.fetchall()
	database.connection.close()
	news = []
	for c in range(len(hot)):
		news_start, news_other = represent_news(hot[c][0])
		news.append('▶ <a href="%s">%s</a> %s' % (hot[c][2], news_start, news_other))
	return '\n\n'.join(news)


def get_other_hot_news():
	database = db.database()
	database.cursor.execute('select * from news where hot_topic>0 and hot_topic<4 order by hot_topic desc;')
	hot = database.cursor.fetchall()
	database.connection.close()
	news = []
	for c in range(len(hot)):
		news_start, news_other = represent_news(hot[c][0])
		news.append('▶ <a href="%s">%s</a> %s' % (hot[c][2], news_start, news_other))
	return '\n\n'.join(news)


def update_clusters():
	news = np.array(db.database().get_news())
	norm_texts = (news[:,1] + ' ' + news[:,4] + ' ' + news[:,8])
	for c in range(len(norm_texts)):
		norm_texts[c] = norm_texts[c].replace('\xa0', ' ')
	tf = TfidfVectorizer()
	texts_transformed = tf.fit_transform(norm_texts)

	Z = linkage(texts_transformed.todense(), 'ward')
	clusters = fcluster(Z, 1.4, criterion='distance')
	database = db.database()
	for c in range(len(news)):
		database.update_news_cluster(news[c][2], clusters[c])
	database.connection.commit()
	database.connection.close()

	print('clusters updated')


def set_hot_news():
	news = np.array(db.database().get_news())
	df = pd.DataFrame(news, columns=['header', 'header_preproc', 'link', 'text', 'text_preproc', 'date', 'source',
		'full_text', 'full_text_preproc', 'cluster', 'hot_topic'])
	cluster_sizes = df.groupby('cluster').count()['header'].values
	avg_time = []
	sources = []
	for c in np.unique(df['cluster']):
		avg_time.append((datetime.now() - df[df['cluster'] == c]['date']).astype('m8[ms]').mean())
		sources.append(np.unique(df[df['cluster'] == c]['source'].values).shape[0])
	time_ind = np.array(avg_time)/max(avg_time)
	news_rate = np.array(cluster_sizes) * np.array((3-time_ind))*(1+np.array(sources)/7)
	clust_rating = np.argsort(news_rate)[::-1] + 1
	database = db.database()
	database.cursor.execute('update news set hot_topic=0;')
	for i, cluster in enumerate((clust_rating[:10])):
		database.cursor.execute("UPDATE news SET hot_topic = %d WHERE link='%s'" % (10-i, get_cl(df[df['cluster'] == cluster]['link'].values)))
	database.connection.commit()
	database.connection.close()
	print('hot news updated')


def get_cl(cluster):
	distances = np.zeros(shape=(len(cluster), len(cluster)))
	for c in range(len(cluster)):
		for d in range(len(cluster)):
			distances[c][d] = distance(cluster[c], cluster[d])
	a = distances.sum(axis=1)
	return cluster[np.argmin(a)]


def distance(a, b):
	"Calculates the Levenshtein distance between a and b."
	n, m = len(a), len(b)
	if n > m:
		a, b = b, a
		n, m = m, n

	current_row = range(n+1)
	for i in range(1, m+1):
		previous_row, current_row = current_row, [i]+[0]*n
		for j in range(1,n+1):
			add, delete, change = previous_row[j]+1, current_row[j-1]+1, previous_row[j-1]
			if a[j-1] != b[i-1]:
				change += 1
			current_row[j] = min(add, delete, change)

	return current_row[n]


def get_random_news():
	database = db.database()
	database.cursor.execute('SELECT * from news order by date desc limit 30;')
	last_news = database.cursor.fetchall()
	database.connection.close()
	rand_news = last_news[np.random.randint(0,30)]

	news_start, news_other = represent_news(rand_news[0])
	news_words = rand_news[7].split()
	full_text = '    ' + ' '.join(news_words[:100])
	if len(news_words) > 100:
		full_text += '... <a href="%s">Читать далее</a>' % (rand_news[2])
	return '🆕 %s, %s: <a href="%s">%s</a> %s \n\n%s' % (rand_news[5].strftime('%Y-%m-%d %H:%M'), rand_news[6],
		rand_news[2], news_start, news_other,  full_text)


def get_rare(chat_id=None):
	database = db.database()
	database.cursor.execute('SELECT cluster from (SELECT count(*) as count, cluster from news GROUP BY cluster order BY count LIMIT 10) as t1;')
	clusters = database.cursor.fetchall()
	clusters = [cluster[0] for cluster in clusters]
	rand_cluster = np.random.choice(clusters)
	database.cursor.execute('select * from news where cluster=%d limit 1;' % rand_cluster)
	rand_news = list(database.cursor.fetchall()[0])
	news_start, news_other = represent_news(rand_news[0])
	news_words = rand_news[7].split()
	full_text = '    ' + ' '.join(news_words[:100])
	if len(news_words) > 100:
		full_text += '... <a href="%s">Читать далее</a>' % (rand_news[2])
	return '🆕 %s, %s: <a href="%s">%s</a> %s \n\n%s' % (rand_news[5].strftime('%Y-%m-%d %H:%M'), rand_news[6],
		rand_news[2], news_start, news_other, full_text)