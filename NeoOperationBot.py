from os import getenv
from dotenv import load_dotenv
import telebot
from telebot import types
import re
from datetime import datetime as dt
from zoneinfo import ZoneInfo
from log_lib import *

ENV_BOTTOKEN = 'BOTTOKEN'
ENV_BOTTOKENTEST = 'BOTTOKENTEST'

ENV_TESTDB = 'TESTDB'
ENV_TESTBOT = 'TESTBOT'

VERSION = '0.1'

CMD_HELP = '/help'
CMD_NEWACTION = '/newaction'
CMD_SHOWACTIONS = '/showactions'
CMD_COMPLETEACTION = '/completeaction'
CMD_CANCELACTION = '/cancelaction'

#============================
# Common functions
#----------------------------
def isTestBot():
    load_dotenv()
    ret = True
    testbot = getenv(ENV_TESTBOT)
    if (testbot):
        if (testbot == "False"):
            ret = False
    return ret

def isTestDB():
    load_dotenv()
    ret = True
    testdb = getenv(ENV_TESTDB)
    if (testdb):
        if (testdb == "False"):
            ret = False
    return ret    

def getBotToken(test):
    load_dotenv()
    token = getenv(ENV_BOTTOKEN)
    if (test):
        token = getenv(ENV_BOTTOKENTEST)

    return token

def getCurrentDateTime():
    tzinfo=ZoneInfo('Europe/Moscow')
    startTime = dt.now(tzinfo).strftime("%d-%m-%Y %H:%M:%S")
    return startTime

#=====================
# Bot class
#---------------------
class NeoOperationBot:
    __bot = None

    def initBot(self):
        # Check if bot is already initialized
        if (NeoOperationBot.isInitialized()):
            log(f'Bot is already initialized', LOG_WARNING)
            return
        # Initialize bot first time
        isTest = isTestBot()
        botToken = getBotToken(isTest)
        if (not botToken):
            log(f'Cannot read ENV vars: botToken={botToken}', LOG_ERROR)
            exit()
        log(f'Bot initialized successfully (test={isTest})')
        NeoOperationBot.__bot = telebot.TeleBot(botToken)
        NeoOperationBot.__bot.register_message_handler(self.messageHandler)
        NeoOperationBot.__bot.register_callback_query_handler(self.buttonHandler,func=lambda message: re.match(fr'^somedata$', message.data))

    def isInitialized():
        return (NeoOperationBot.__bot != None)

    # Init bot
    def __init__(self):
        # Check if bot is initialized
        if (not NeoOperationBot.isInitialized()):
            NeoOperationBot.initBot(self)
        self.bot = NeoOperationBot.__bot

    def startBot(self):
        if (not NeoOperationBot.isInitialized()):
            log(f'Bot is not initialized - cannot start', LOG_ERROR)
            return
        try:
            log(f'Starting bot...')
            #self.bot.set_update_listener(self.get_messages)
            self.bot.infinity_polling()
        except KeyboardInterrupt:
            log('Exiting by user request')

    # Get default title
    def getDefaultTitle(self):
        datetimenow = getCurrentDateTime()
        return f"Action from {datetimenow}"

    # Message handler
    def messageHandler(self, message):
        if (not NeoOperationBot.isInitialized()):
            log(f'Bot is not initialized - cannot start', LOG_ERROR)
            return
        # Check if there is a CMD
        if (message.text[0] == '/'):
            return self.cmdHandler(message)
        NeoOperationBot.__bot.send_message(message.from_user.id, 'Я вас не понимаю:(.')
        NeoOperationBot.__bot.send_message(message.from_user.id, self.getHelpMessage(message.from_user.username))

    def cmdHandler(self, message):
        bot = NeoOperationBot.__bot
        text = message.text.lower()
        if text == CMD_HELP:
            bot.send_message(message.from_user.id, self.getHelpMessage(message.from_user.username))
        elif text == CMD_NEWACTION:
            self.newActionHandler(message)
        elif text == CMD_SHOWACTIONS:
            self.showActionsHandler(message)
        elif text == CMD_COMPLETEACTION:
            self.completeActionHandler(message)
        elif text == CMD_CANCELACTION:
            self.cancelActionHandler(message)
        else:
            bot.send_message(message.from_user.id, "Неизвестная команда.")
            bot.send_message(message.from_user.id, self.getHelpMessage(message.from_user.username))

    # Returns help message
    def getHelpMessage(self, userName):
        if (not NeoOperationBot.isInitialized()):
            log(f'Bot is not initialized - cannot start', LOG_ERROR)
            return
        ret = self.getWelcomeMessage(userName)
        return ret + '''
    Команды GuessImage_Bot:
        /help - вывести помощь по каомандам (это сообщение)
        /start - начать новую игру с текущими настройками (может вызываться на любом шаге)
        /settings - установить настройки типа игры и сложности
        '''
    # Get welcome message
    def getWelcomeMessage(self, userName):
        ret = f'''
        Добро пожаловать, {userName}!
        Это боте "Neo Operation". Версия: {VERSION}
        '''
        return ret

    # Test button
    def showTestButton(self, message):
        key1 = types.InlineKeyboardButton(text='Кнопка 1', callback_data="somedata")
        key2 = types.InlineKeyboardButton(text='Кнопка 2', callback_data="somedata2")
        keyboard = types.InlineKeyboardMarkup(); # keyboard
        keyboard.add(key1)
        keyboard.add(key2)
        question = 'Что дальше?'
        self.bot.send_message(message.from_user.id, text=question, reply_markup=keyboard)

    def buttonHandler(self, message):
        self.bot.send_message(message.from_user.id, f"Button pressed.{message.data}")

    def newActionHandler(self, message):
        if (not NeoOperationBot.isInitialized()):
            log(f'Bot is not initialized - cannot start', LOG_ERROR)
            return
        self.bot.send_message(message.from_user.id, f"Пожалуйста, введите тескт задачи:")
        # TODO: save current status - inputaction

    def showActionsHandler(self, message):
        pass

    def completeActionHandler(self, message):
        pass

    def cancelActionHandler(self, message):
        pass