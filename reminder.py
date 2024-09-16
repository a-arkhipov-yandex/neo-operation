from datetime import datetime
from time import sleep
import telebot
from telegram import Message, User, Chat
from db_lib import *
from log_lib import *
from NeoOperationBot import *

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
            actionId = actionInfo['id']
            username = actionInfo['username']
            telegramid = actionInfo['telegramid']
            reminderText = "\U00002757 Reminder:" + getActionInfoText(actionInfo=actionInfo)
            bot.send_message(telegramid, reminderText)
            # Show actions to do with reminder: remind later, mark completed, mark cancelled
            menuKeyboard = getActionMenu(actionId=actionId,reminder=True)
            message = bot.send_message(telegramid, text='Выберите действие с задачей:', reply_markup=menuKeyboard)
            message_id = message.id
            chat_id = message.chat.id
            # Save chat_id and message_id to hide later
            Connection.udpdateActionButtons(username=username,actionId=actionId,buttons=f'{message_id}|{chat_id}')
            # Mark reminder as shown
            Connection.markReminderAsShown(username=username,actionId=actionId)
        lenReminders = len(actions)
        if (lenReminders != 0):
            log(f'{fName}: Handled {lenReminders} reminders. Sleeping...')
    log(f'{fName}: Reminder thread stopped')
