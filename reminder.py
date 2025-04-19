from time import sleep
import telebot
from db_lib import *
from log_lib import *
from NeoOperationBot import *

loopFlag = True
SLEEP_INTERVAL = 5

def reminderTask(bot:telebot.TeleBot) -> None:
    fName = reminderTask.__name__
    log(str=f'{fName}: Reminder thread is started')
    # infinite loop
    while(loopFlag):
        sleep(SLEEP_INTERVAL)
        # Get all actions with reminders
        actions = Connection.getActionsWithExpiredReminders()
        if (not actions):
            continue
        handled = 0
        for actionInfo in actions:
            actionId = actionInfo['id']
            username = actionInfo['username']
            telegramid = actionInfo['telegramid']
            reminderText = "\U00002757 Reminder:"
            if (showActionMenu(bot=bot, actionInfo=actionInfo, telegramid=telegramid, addText=reminderText)):
                # Mark reminder as shown
                Connection.markReminderAsShown(username=username,actionId=actionId)
            handled += 1
        lenReminders = len(actions)
        log(str=f'{fName}: Got {lenReminders} reminders. Handled {lenReminders} reminders. Sleeping...')
    log(str=f'{fName}: Reminder thread stopped')
