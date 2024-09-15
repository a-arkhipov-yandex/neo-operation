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
        # Get all actions with reminders
        actions = Connection.getActionsWithExpiredReminders()
        for actionInfo in actions:
            bot.send_message(actionInfo['telegramid'], f'Reminder: Action: {actionInfo["title"]}')
            # TODO: make more fancy message

            # Show actions to do with reminder: remind later, mark completed, mark cancelled

            # Clear reminder
            Connection.clearReminder(username=actionInfo['username'], actionId=actionInfo['id'])

            # TODO: Remove keyboard buttons after pressing
            pass
        lenReminders = len(actions)
        if (lenReminders != 0):
            log(f'{fName}: Handled {lenReminders} reminders. Sleeping...')
    log(f'{fName}: Reminder thread stopped')
