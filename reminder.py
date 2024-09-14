from datetime import datetime
from time import sleep
import telebot
from telegram import Message, User, Chat
from db_lib import *
from log_lib import *

loopFlag = True
SLEEP_INTERVAL = 10


def reminderTask(bot:telebot.TeleBot):
    fName = reminderTask.__name__
    log(f'{fName}: Reminder thread is started')
    # infinite loop
    while(loopFlag):
        sleep(SLEEP_INTERVAL)
        log(f'{fName}: Reminder task wake up...')
        # Get all actions with reminders
        actions = Connection.getActions(withReminders=True, active=True)
        for actionInfo in actions:
            bot.send_message(actionInfo['telegramid'], f'Reminder: Action: {actionInfo["title"]}')
            # TODO: make more fancy message

            # Show actions to do with reminder: remind later, mark completed, mark cancelled

            # TODO: Remove keyboard buttons after pressing
            pass
        lenReminders = len(actions)
        log(f'Handled {lenReminders} reminders. Sleeping...')
    log(f'{fName}: Reminder thread stopped')
