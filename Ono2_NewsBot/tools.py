import requests
from bs4 import BeautifulSoup
import json
import datetime
import locale
import news


def upd_dollar_rate_and_weather(bot, update):
	raw_html = requests.get('http://yandex.ru').text
	bs4 = BeautifulSoup(raw_html, 'lxml')
	dollar_rate = bs4.find_all('span', 'inline-stocks__value_inner')[0].text
	weather_now = bs4.find_all('a', 'home-link home-link_black_yes')[0]['aria-label']

	info_dict = {'dollar_rate':dollar_rate, 'weather_now':weather_now}
	info_json = json.dumps(info_dict, ensure_ascii=False)
	with open('data/info.json', 'w') as file:
		file.write(info_json)


def good_morning():
	with open('data/info.json', 'r') as file:
		info_dict = file.read()
	info_dict = json.loads(info_dict)
	date = datetime.date.today()
	return ('Доброе утро! Сегодня %d.%d.\nПогода в Москве: %s.\n💲Курс доллара: %s.\n%s') % (date.day, date.month, info_dict['weather_now'], info_dict['dollar_rate'], news.get_hot_news())
