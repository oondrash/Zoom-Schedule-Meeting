import time
from datetime import datetime
from pynput.keyboard import Controller, Key
from config import schedule, user_ids, TOKEN, NAME, SURNAME, GROUP, CHAT_KEY, LEAVE_KEY
import webbrowser
import telebot
import threading

bot = telebot.TeleBot(TOKEN)
keyboard = Controller()
is_started = False
chat_opened = False
dropped_by_user = False


def user_access_check(func):
    def wrapper(message):
        user = message.from_user.id
        if user not in user_ids:
            bot.send_message(message.chat.id, "У вас немає доступу до цієї команди")
            return
        func(message)

    return wrapper


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Старт")


@bot.message_handler(commands=['fullname'])
@user_access_check
def fullname(message):
    global keyboard, is_started, chat_opened
    if is_started:
        if not chat_opened:
            keyboard.press(CHAT_KEY)
            chat_opened = True
            time.sleep(1)
        keyboard.type(f"{SURNAME} {NAME} {GROUP}")
        time.sleep(1)
        keyboard.press(Key.enter)
        bot.send_message(message.chat.id, "ПІБ відправлено")


@bot.message_handler(commands=['surname'])
@user_access_check
def surname(message):
    global keyboard, is_started, chat_opened
    if is_started:
        if not chat_opened:
            keyboard.press(CHAT_KEY)
            chat_opened = True
            time.sleep(1)
        keyboard.type(f"{SURNAME} {GROUP}")
        time.sleep(1)
        keyboard.press(Key.enter)
        bot.send_message(message.chat.id, "Прізвище відправлено")


@bot.message_handler(commands=["drop"])
@user_access_check
def drop(message):
    global keyboard, is_started, chat_opened, dropped_by_user
    if is_started:
        keyboard.press(LEAVE_KEY)
        time.sleep(1)
        keyboard.press(Key.enter)
        is_started = False
        chat_opened = False
        dropped_by_user = True
        bot.send_message(message.chat.id, "Ви вийшли з конференції")


@bot.message_handler(commands=["chat"])
@user_access_check
def chat(message):
    global keyboard, is_started, chat_opened
    if not chat_opened:
        keyboard.press(CHAT_KEY)
        chat_opened = True
    keyboard.type(message.text[6:])
    time.sleep(1)
    keyboard.press(Key.enter)
    bot.send_message(message.chat.id, "Повідомлення відправлено")


@bot.message_handler(commands=["join"])
@user_access_check
def join(message):
    global keyboard, is_started, chat_opened
    webbrowser.open(message.text[6:])
    chat_opened = False
    is_started = True
    bot.send_message(message.chat.id, "Підключено до конференції")


threading.Thread(target=bot.polling, kwargs={"none_stop": True}).start()


def meeting_running(start_time: str, end_time: str):
    start_time = datetime.strptime(start_time, "%H:%M")
    end_time = datetime.strptime(end_time, "%H:%M")
    now = datetime.now().strptime(datetime.now().strftime("%H:%M"), "%H:%M")
    if start_time <= now <= end_time:
        return True
    return False


for i in schedule:
    while True:
        if not is_started:
            if dropped_by_user:
                dropped_by_user = False
                break
            if meeting_running(i[1], i[2]):
                webbrowser.open(i[0])
                is_started = True
        else:
            if not meeting_running(i[1], i[2]):
                keyboard.press(LEAVE_KEY)
                time.sleep(1)
                keyboard.press(Key.enter)
                is_started = False
                break
        time.sleep(5)
