import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import F

API_TOKEN = '7332057477:AAELBacAFeF6hFrI2frI-VV53z6mQ0lfV6E'

# Bot va Dispatcher
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
scheduler = AsyncIOScheduler()

# Vazifalarni saqlash uchun dictionary
tasks = {}

# Soat tanlash uchun klaviatura
def hour_keyboard(user_id):
    keyboard = [
        [KeyboardButton(text=f"{hour:02d}:00")] for hour in range(24)
    ]
    user_tasks = tasks.get(user_id, [])
    if user_tasks:
        task_buttons = [KeyboardButton(text=f"{task['start_time'].strftime('%H:%M')} - {task['end_time'].strftime('%H:%M')} - {task['task']}") for task in user_tasks]
        keyboard.extend(task_buttons)
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# Vazifalarni ko'rsatish uchun funksiya
def show_tasks(user_id):
    now = datetime.now()
    user_tasks = tasks.get(user_id, [])
    task_list = [f"{task['start_time'].strftime('%H:%M')} - {task['end_time'].strftime('%H:%M')} - {task['task']}" for task in user_tasks if task['end_time'] > now]
    return "\n".join(task_list) if task_list else "Rejalashtirilgan vazifalar yo'q."

# Start komanda
@dp.message(F.text == "/start")
async def send_welcome(message: types.Message):
    await message.reply("Kun tartibini rejalashtirish botiga xush kelibsiz!\nKerakli soatni tanlang:", reply_markup=hour_keyboard(message.from_user.id))

# Soat tanlash
@dp.message(lambda message: message.text and ":" in message.text)
async def set_hour(message: types.Message):
    user_id = message.from_user.id
    if user_id not in tasks:
        tasks[user_id] = []
    task_time = datetime.strptime(message.text, "%H:%M").replace(year=datetime.now().year, month=datetime.now().month, day=datetime.now().day)
    tasks[user_id].append({'start_time': task_time})
    await message.reply("Davomiyligini daqiqalarda kiriting:", reply_markup=types.ReplyKeyboardRemove())

# Davomiylik tanlash
@dp.message(lambda message: message.text.isdigit())
async def set_duration(message: types.Message):
    user_id = message.from_user.id
    if tasks[user_id] and 'start_time' in tasks[user_id][-1]:
        duration = int(message.text)
        tasks[user_id][-1]['duration'] = duration
        tasks[user_id][-1]['end_time'] = tasks[user_id][-1]['start_time'] + timedelta(minutes=duration)
        await message.reply("Vazifani yozing:", reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.reply("Iltimos, avval soatni tanlang.")

# Vazifani belgilash
@dp.message(lambda message: tasks.get(message.from_user.id) and 'duration' in tasks[message.from_user.id][-1])
async def set_task(message: types.Message):
    user_id = message.from_user.id
    task_description = message.text
    tasks[user_id][-1]['task'] = task_description

    # Eslatma uchun rejalashtirish
    scheduler.add_job(send_notification, 'date', run_date=tasks[user_id][-1]['start_time'], args=[user_id, task_description])
    await message.reply(f"Vazifa belgilandi: {task_description} soat {tasks[user_id][-1]['start_time'].strftime('%H:%M')} dan {tasks[user_id][-1]['end_time'].strftime('%H:%M')} gacha\n{show_tasks(user_id)}", reply_markup=hour_keyboard(user_id))

# Eslatma yuborish
async def send_notification(user_id, task_description):
    await bot.send_message(user_id, f"Eslatma: {task_description}")

async def on_startup(dispatcher):
    scheduler.start()

async def on_shutdown(dispatcher):
    await bot.session.close()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.run_polling(bot)
