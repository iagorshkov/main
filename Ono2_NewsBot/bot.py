import mysql.connector
import db
import news
import social
import os
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, Job, CallbackQueryHandler
from telegram import replykeyboardmarkup, InlineKeyboardButton, InlineKeyboardMarkup
from time import strftime

os.environ['TZ'] = 'Europe/Moscow'


keyboard = replykeyboardmarkup.ReplyKeyboardMarkup([['Что нового?', 'Что интересного?', 'Поговори со мной']], resize_keyboard=1)



#Hadlers:
def start(bot, update):
	bot.sendMessage(chat_id=update.message.chat_id, text="Привет! Я новостной бот! Вот, на что я умею отвечать:", reply_markup=keyboard)


def get_stat(bot, update):
	bot.sendMessage(chat_id=update.message.chat_id, text=db.database().get_chat_stat(update.message.chat_id), reply_markup=keyboard)


def messages(bot, update):

	database = db.database()

	if update.message.text == 'Что нового?':
		result = news.get_random_news(update.message.chat_id, use_db=True)
		database.add_query([update.message.chat_id, update.message.text, result, strftime("%Y-%m-%d %H:%M:%S")])
		bot.sendMessage(chat_id=update.message.chat_id, text = result, reply_markup=keyboard)

	elif update.message.text == 'Что интересного?':
		top_tags = news.get_tags()
		tags_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(top_tags[0], callback_data=top_tags[0]),
                 InlineKeyboardButton(top_tags[1], callback_data=top_tags[1]),
                 InlineKeyboardButton(top_tags[2], callback_data=top_tags[2])],
                 [InlineKeyboardButton(top_tags[3], callback_data=top_tags[3]), 
                 InlineKeyboardButton(top_tags[4], callback_data=top_tags[4])]])
		update.message.reply_text('Обсуждают прямо сейчас (кликните, чтоб получить новость по тегу):', reply_markup=tags_keyboard)

	elif update.message.text == 'Поговори со мной':
		result = social.start_talk()
		database.add_query([update.message.chat_id, update.message.text, result, strftime("%Y-%m-%d %H:%M:%S")])
		bot.sendMessage(chat_id=update.message.chat_id, text = result, reply_markup=keyboard)


def button(bot, update):
	result = news.get_news_by_tag(update.callback_query.data)
	bot.sendMessage(chat_id=update.callback_query.message.chat.id, text=result, reply_markup=keyboard)



def main():

	updater = Updater(token='318966182:AAFETX_PVNor5CXXEROgJMMQsCbeL_dnekI')
	dispatcher = updater.dispatcher
	

	dispatcher.add_handler(CommandHandler('start', start))
	dispatcher.add_handler(CommandHandler('stat', get_stat))
	dispatcher.add_handler(MessageHandler(Filters.text, messages))
	dispatcher.add_handler(CallbackQueryHandler(button))


	job_queue = updater.job_queue


	REMINDER_PERIOD = 60.0
	reminder = Job(db.remind, REMINDER_PERIOD)
	job_minute = Job(news.upd_news, 60.0)


	job_queue.put(job_minute, next_t=0.0)
	job_queue.put(reminder, next_t=0.0)


	updater.start_polling()

	updater.idle()

if __name__ == '__main__':
	main()
