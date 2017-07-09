import db
import news
import news_dump
import os
import tools
import json
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, Job, CallbackQueryHandler
from telegram import replykeyboardmarkup, InlineKeyboardButton, InlineKeyboardMarkup
from time import strftime
from datetime import time
import locale
import botan

os.environ['TZ'] = 'Europe/Moscow'
locale.setlocale(locale.LC_ALL, 'en_US.utf8')

keyboard = replykeyboardmarkup.ReplyKeyboardMarkup([['Новое', 'Главное', '🎲🎲']], resize_keyboard=1)


def start(bot, update):
	bot.sendMessage(chat_id=update.message.chat_id, text="Привет! Я новостной бот! Вот, на что я умею отвечать:", reply_markup=keyboard)


def get_stat(bot, update):
	bot.sendMessage(chat_id=update.message.chat_id, text=db.database().get_chat_stat(update.message.chat_id), reply_markup=keyboard)


def do_news_dump(bot, update):
	user_id = update.message.chat_id
	if user_id == 451162:
		news_dump.send_news()
		bot.sendMessage(chat_id=user_id, text='Successful')


def messages(bot, update):

	#with open('config.json', 'r') as file:
	#	botan_token = json.loads(file.read())['botan_token']
	#uid = update.message.chat_id
	#message_dict = update.message.to_dict()
	#event_name = update.message.text
	#botan.track(botan_token, uid, message_dict, event_name)

	db.database().save_user_mess([update.message.chat_id, update.message.text, strftime("%Y-%m-%d %H:%M:%S")])

	if update.message.text == 'Новое':
		text = news.get_random_news()
		smiles_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("👍", callback_data="Like"), 
			InlineKeyboardButton("❤", callback_data="Love"), InlineKeyboardButton("😂", callback_data="Haha"),
			InlineKeyboardButton("😊", callback_data="Yay"), InlineKeyboardButton("😱", callback_data="Wow"),
			InlineKeyboardButton("😩", callback_data="Sad"),InlineKeyboardButton("😡", callback_data="Angry")]])
		bot.sendMessage(chat_id=update.message.chat_id, text = text, parse_mode='html', disable_web_page_preview=1,
			reply_markup=smiles_keyboard)

	elif update.message.text == 'Главное':
		headers = news.get_hot_news()
		more_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Еще...", callback_data='More')]])
		bot.sendMessage(chat_id=update.message.chat_id, text = headers, reply_markup=more_keyboard, parse_mode='html',
			disable_web_page_preview=1)

	elif update.message.text == '🎲🎲':
		text = news.get_rare(chat_id=update.message.chat_id)
		smiles_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("👍", callback_data="Like"), 
			InlineKeyboardButton("❤", callback_data="Love"), InlineKeyboardButton("😂", callback_data="Haha"),
			InlineKeyboardButton("😊", callback_data="Yay"), InlineKeyboardButton("😱", callback_data="Wow"),
			InlineKeyboardButton("😩", callback_data="Sad"),InlineKeyboardButton("😡", callback_data="Angry")]])
		bot.sendMessage(chat_id=update.message.chat_id, text = text, parse_mode='html',
			disable_web_page_preview=1, reply_markup=smiles_keyboard)


def button(bot, update):
	if update.callback_query.data == 'More':
		headers = news.get_other_hot_news()
		bot.editMessageReplyMarkup(chat_id=update.callback_query.message.chat.id,
			message_id=update.callback_query.message.message_id, reply_markup='')
		bot.sendMessage(chat_id=update.callback_query.message.chat.id, text = headers, reply_markup=keyboard, parse_mode='html',
			disable_web_page_preview=1)
	else:
		bot.editMessageReplyMarkup(chat_id=update.callback_query.message.chat.id,
			message_id=update.callback_query.message.message_id, reply_markup='')


def update_all(bot, update):
	news.upd_news()
	news.update_clusters()
	news.set_hot_news()


def good_morning(bot, update):
	user_ids = db.database().get_user_ids()
	for user_id in user_ids:
		more_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Еще...", callback_data='More')]])
		bot.sendMessage(chat_id=user_id[0], text=tools.good_morning(), reply_markup=more_keyboard, parse_mode='html',
			disable_web_page_preview=1)

def main():
	with open('config.json', 'r') as file:
		TOKEN = json.loads(file.read())['bot_token']
	updater = Updater(token=TOKEN)
	dispatcher = updater.dispatcher
	
	dispatcher.add_handler(CommandHandler('start', start))
	dispatcher.add_handler(CommandHandler('stat', get_stat))
	dispatcher.add_handler(CommandHandler('dump', do_news_dump))
	dispatcher.add_handler(MessageHandler(Filters.text, messages))
	dispatcher.add_handler(CallbackQueryHandler(button))

	job_queue = updater.job_queue

	REMINDER_PERIOD = 120.0

	job_queue.put(Job(db.remind, REMINDER_PERIOD), next_t=0.0)
	job_queue.put(Job(update_all, 900.0), next_t=0.0)
	job_queue.run_daily(tools.upd_dollar_rate_and_weather, time(hour=5, minute=50))
	job_queue.run_daily(good_morning, time(hour=6))

	updater.start_polling()

	updater.idle()

if __name__ == '__main__':
	main()