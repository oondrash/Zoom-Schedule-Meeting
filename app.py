import time
from datetime import datetime
from pynput.keyboard import Controller, Key
from config import schedule, user_ids, TOKEN, NAME, SURNAME, GROUP, CHAT_KEY, LEAVE_KEY, FULL_SCREEN_KEY
import webbrowser
import telebot
import threading
import pygetwindow as gw


class ZoomRemoteControl:

    def __init__(self,
                 token,
                 name,
                 surname,
                 group,
                 chat_key,
                 leave_key,
                 full_screen_key,
                 schedule_list,
                 user_ids_list):

        self.token = token

        self.name = name
        self.surname = surname
        self.group = group

        self.chat_key = chat_key
        self.leave_key = leave_key
        self.full_screen_key = full_screen_key

        self.schedule = schedule_list
        self.user_ids = user_ids_list

        self.is_started = lambda: bool(gw.getWindowsWithTitle("Zoom Meeting"))

        self.dropped_by_user = False

        self.keyboard = Controller()
        self.bot = telebot.TeleBot(self.token)
        self.zoom = lambda: gw.getWindowsWithTitle("Zoom Meeting")[0]

    @staticmethod
    def validate_zoom_schedule(schedule_list):
        for meeting in schedule_list:
            # Check if meeting link is valid
            if not meeting[0].startswith("https://us"):
                raise ValueError("Invalid meeting link")
            # Check if meeting start time is valid
            try:
                datetime.strptime(meeting[1], "%H:%M")
            except ValueError:
                raise ValueError("Invalid meeting start time")
            # Check if meeting end time is valid
            try:
                datetime.strptime(meeting[2], "%H:%M")
            except ValueError:
                raise ValueError("Invalid meeting end time")
            # Check if meeting start time is before end time
            if datetime.strptime(meeting[1], "%H:%M") >= datetime.strptime(meeting[2], "%H:%M"):
                raise ValueError("Meeting start time must be before end time")
            # check for overlapping meetings
            for meeting2 in schedule_list:
                if meeting == meeting2:
                    continue
                if datetime.strptime(meeting[1], "%H:%M") <= datetime.strptime(meeting2[1],
                                                                               "%H:%M") <= datetime.strptime(meeting[2],
                                                                                                             "%H:%M"):
                    raise ValueError("Meetings must not overlap")
                if datetime.strptime(meeting[1], "%H:%M") <= datetime.strptime(meeting2[2],
                                                                               "%H:%M") <= datetime.strptime(meeting[2],
                                                                                                             "%H:%M"):
                    raise ValueError("Meetings must not overlap")

    def set_commands(self):
        def access_check(func):
            def wrapper(message):
                user = message.from_user.id
                if user not in self.user_ids:
                    self.bot.send_message(message.chat.id, "У вас немає доступу до цієї команди")
                    return
                func(message)

            return wrapper

        @self.bot.message_handler(commands=['start'])
        @access_check
        def start(message):
            self.bot.send_message(message.chat.id, "Початок роботи")

        @self.bot.message_handler(commands=['fullname'])
        @access_check
        def fullname(message):
            if not self.is_started():
                self.bot.send_message(message.chat.id, f"{NAME} не приймає участі в жодній зустрічі")
                return

            self.open_chat()
            self.keyboard.type(f"{self.surname} {self.name} {self.group}")
            time.sleep(1)
            self.keyboard.press(Key.enter)
            self.bot.send_message(message.chat.id, "ПІБ відправлено")

        @self.bot.message_handler(commands=['surname'])
        @access_check
        def surname(message):
            if not self.is_started():
                self.bot.send_message(message.chat.id, f"{NAME} не приймає участі в жодній зустрічі")
                return


            self.open_chat()

            self.keyboard.type(f"{self.surname} {self.group}")
            time.sleep(1)
            self.keyboard.press(Key.enter)
            self.bot.send_message(message.chat.id, "Прізвище відправлено")

        @self.bot.message_handler(commands=['leave'])
        @access_check
        def leave(message):
            if not self.is_started():
                self.bot.send_message(message.chat.id, f"{NAME} не приймає участі в жодній зустрічі")
                return
            else:
                if not self.zoom().isActive:
                    self.zoom().activate()

            self.keyboard.press(self.leave_key)
            self.bot.send_message(message.chat.id, "Ви вийшли зі зустрічі")
            self.dropped_by_user = True

        @self.bot.message_handler(commands=['chat'])
        @access_check
        def chat(message):
            if not self.is_started():
                self.bot.send_message(message.chat.id, f"{NAME} не приймає участі в жодній зустрічі")
                return

            self.open_chat()

            self.keyboard.type(message.text[6:])
            time.sleep(1)
            self.keyboard.press(Key.enter)
            self.bot.send_message(message.chat.id, "Повідомлення відправлено")

        @self.bot.message_handler(commands=['join'])
        @access_check
        def join(message):
            if self.is_started():
                self.bot.send_message(message.chat.id,
                                      f"{NAME} вже приймає участь в зустрічі. Використайте команду /leave, щоб вийти з"
                                      f" поточної зустрічі")
                return
            else:
                webbrowser.open(message.text[6:])
                time.sleep(3)
                self.bot.send_message(message.chat.id, "Ви приєднались до зустрічі")

    @staticmethod
    def meeting_running(start_time: str, end_time: str):
        start_time = datetime.strptime(start_time, "%H:%M")
        end_time = datetime.strptime(end_time, "%H:%M")
        now = datetime.now().strptime(datetime.now().strftime("%H:%M"), "%H:%M")
        if start_time <= now <= end_time:
            return True
        return False

    @staticmethod
    def is_fullscreen():
        # Get the specified application window
        windows = gw.getWindowsWithTitle("Zoom Meeting")
        if not windows:
            return False
        window = windows[0]

        # Get the screen's width and height
        screen_width = gw.getWindowsAt(0, 0)[0]._rect.width
        print(screen_width)
        print(window.width)
        screen_height = gw.getWindowsAt(0, 0)[0]._rect.height
        print(screen_height)
        print(window.height)

        # Check if the window dimensions match the screen size
        return window.width + 14 == screen_width and window.height == screen_height + 34

    @staticmethod
    def chat_is_opened():
        windows = gw.getWindowsWithTitle("")
        for window in windows:
            if window.area == 143560:
                return True
        return False

    def open_chat(self):
        if not self.zoom().isActive:
            print("activate")
            self.zoom().activate()
            time.sleep(1)
        if not self.is_fullscreen():
            self.keyboard.press(self.full_screen_key)
            time.sleep(1)
        self.keyboard.press(self.chat_key)
        return



    def run(self):
        self.set_commands()
        threading.Thread(target=self.bot.polling, kwargs={"none_stop": True}).start()

        for meeting in self.schedule:
            while True:
                if not self.is_started():
                    if self.dropped_by_user:
                        self.dropped_by_user = False
                        break
                    if self.meeting_running(meeting[1], meeting[2]):
                        webbrowser.open(meeting[0])
                        time.sleep(3)
                else:
                    if not self.meeting_running(meeting[1], meeting[2]):
                        if not self.zoom().isActive:
                            self.zoom().activate()
                        time.sleep(1)
                        self.keyboard.press(self.leave_key)
                        self.dropped_by_user = False
                        break
                    else:
                        if not gw.getWindowsWithTitle("Zoom Meeting"):
                            self.dropped_by_user = False
                            break


if __name__ == '__main__':
    app = ZoomRemoteControl(TOKEN, NAME, SURNAME, GROUP, CHAT_KEY, LEAVE_KEY, FULL_SCREEN_KEY, schedule, user_ids)
    app.run()
