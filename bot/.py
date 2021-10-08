import config
import logging
import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, executor, types
from sqlighter import SQLighter

from sait import sait

# задаем уровень логов
logging.basicConfig(level=logging.INFO)

# инициализируем бота xyi
bot = Bot(token=config.API_TOKEN)
dp = Dispatcher(bot)

# инициализируем соединение с БД
db = SQLighter('db.db')

# инициализируем парсер
sg = plumgun('lastkey.txt')

# Команда активации подписки
@dp.message_handler(commands=['subscribe'])
async def subscribe(message: types.Message):
	if(not db.subscriber_exists(message.from_user.id)):
		# если юзера нет в базе, добавляем его
		db.add_subscriber(message.from_user.id)
	else:
		# если он уже есть, то просто обновляем ему статус подписки
		db.update_subscription(message.from_user.id, True)
	
	await message.answer("Вы успешно подписались ")

# Команда отписки
@dp.message_handler(commands=['unsubscribe'])
async def unsubscribe(message: types.Message):
	if(not db.subscriber_exists(message.from_user.id)):
		# если юзера нет в базе, добавляем его с неактивной подпиской (запоминаем)
		db.add_subscriber(message.from_user.id, False)
		await message.answer("Вы итак не подписаны.")
	else:
		# если он уже есть, то просто обновляем ему статус подписки
		db.update_subscription(message.from_user.id, False)
		await message.answer("Вы успешно отписались ")

# проверяем наличие новых игр и делаем рассылки
async def scheduled(wait_for):
	while True:
		await asyncio.sleep(wait_for)

		# проверяем наличие новых игр
		new_post = sg.new_post()

		if(new_post):
			# если игры есть, переворачиваем список и итерируем
			new_post.reverse()
			for ng in new_post:
				# парсим инфу о новой игре
				nfo = sg.post_info(ng)

				# получаем список подписчиков бота
				subscriptions = db.get_subscriptions()

				# отправляем всем новость
				with open(sg.download_image(nfo['image']), 'rb') as photo:
					for s in subscriptions:
						await bot.send_photo(
							s[1],
							photo,
							caption = nfo['title'] + "\n" + "Оценка: " + nfo['score'] + "\n" + nfo['excerpt'] + "\n\n" + nfo['link'],
							disable_notification = True
						)
				
				# обновляем ключ
				sg.update_lastkey(nfo['id'])

#  лонг поллинг
if __name__ == '__main__':
	dp.loop.create_task(scheduled(60)) 
	executor.start_polling(dp, skip_updates=True)
