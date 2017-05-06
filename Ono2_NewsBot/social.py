from random import choice

def start_talk():
	ans = ['Как дела?', 'А что тебя беспокоит?', 'Сейчас не могу, давай чуть позже', 'Что-то случилось?']
	return choice(ans)