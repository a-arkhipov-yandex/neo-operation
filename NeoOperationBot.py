from os import getenv
from dotenv import load_dotenv
import telebot
from telebot import types
import re
from datetime import datetime as dt
from zoneinfo import ZoneInfo
from log_lib import *
from db_lib import *

ENV_BOTTOKEN = 'BOTTOKEN'
ENV_BOTTOKENTEST = 'BOTTOKENTEST'

ENV_TESTDB = 'TESTDB'
ENV_TESTBOT = 'TESTBOT'

VERSION = '0.1'

CMD_START = '/start'
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
        # Handle reply
        ret = self.replyHandler(message)
        if (not ret):
            self.sendMessage(message.from_user.id, 'Я вас не понимаю:(.')
            self.sendMessage(message.from_user.id, self.getHelpMessage(message.from_user.username))

    # Check is user registered
    def checkUser(self, username):
        userId = Connection.getUserIdByName(username)
        if (dbFound(userId)):
            return True
        return False

    # Send message to user
    def sendMessage(self, telegramid, text):
        if (NeoOperationBot.isInitialized()):
            NeoOperationBot.__bot.send_message(telegramid, text)

    def replyHandler(self, message):
        # Check current user state
        username = message.from_user.username
        id = message.from_user.id
        if (not self.checkUser(username=username)):
            self.sendMessage(id, f'Пользователь не зарегистрирован. Пожалуйста, введите "{CMD_START}"')
            return False
        state = Connection.getUserState(username)
        if (state == STATE_ACTIONTEXT):
            title = self.getDefaultTitle()
            text = message.text
            Connection.addAction(username=username,title=title, text=text, fromTxt='')
            Connection.clearUserState(username=username)
            self.sendMessage(id, 'Новая задача создана успешно.')
            return True
        return False # Nothing to handle

    def startHandler(self, message):
        username = message.from_user.username
        telegramId = message.from_user.id
        # Check if user exists
        if (not self.checkUser(username=username)):
            # Register new user if not registered yet
            userId = Connection.addUser(username=username, telegramid=telegramId)
            if (not userId):
                log(f'Cannot register user {username}', LOG_ERROR)
                self.sendMessage(telegramId, 'Ошибка при регистоации пользователя. Попробуйте позже.')
            # Send welcome message
            self.sendMessage(telegramId, 'Регистрация пользователя прошла успешно.')
            self.helpHandler(message)
        else:
            # Show help message
            self.helpHandler(message)

    def cmdHandler(self, message):
        telegramid = message.from_user.id
        text = message.text.lower()
        if text == CMD_HELP:
            self.helpHandler(message)
        elif text == CMD_START:
            self.startHandler(message)
        elif text == CMD_NEWACTION:
            self.newActionHandler(message)
        elif text == CMD_SHOWACTIONS:
            self.showActionsHandler(message)
        elif text == CMD_COMPLETEACTION:
            self.completeActionHandler(message)
        elif text == CMD_CANCELACTION:
            self.cancelActionHandler(message)
        else:
            self.sendMessage(telegramid, "Неизвестная команда.")
            self.sendMessage(telegramid, self.getHelpMessage(message.from_user.username))

    # /help cmd handler
    def helpHandler(self, message):
        self.sendMessage(message.from_user.id, self.getHelpMessage(message.from_user.username))

    # Returns help message
    def getHelpMessage(self, userName):
        if (not NeoOperationBot.isInitialized()):
            log(f'Bot is not initialized - cannot start', LOG_ERROR)
            return
        ret = self.getWelcomeMessage(userName)
        return ret + f'''
    Команды GuessImage_Bot:
        {CMD_HELP} - вывести помощь по командам (это сообщение)
        {CMD_START} - регистрация нового пользователя
        {CMD_NEWACTION} - создать новую задачу
        {CMD_SHOWACTIONS} - вывести все активные задачи
        '''
    # Get welcome message
    def getWelcomeMessage(self, userName):
        ret = f'''
        Добро пожаловать, {userName}!
        Это бот "Neo Operation". Версия: {VERSION}
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
        self.sendMessage(message.from_user.id, text=question, reply_markup=keyboard)

    def buttonHandler(self, message):
        self.sendMessage(message.from_user.id, f"Button pressed.{message.data}")

    def newActionHandler(self, message):
        if (not NeoOperationBot.isInitialized()):
            log(f'Bot is not initialized - cannot start', LOG_ERROR)
            return
        self.sendMessage(message.from_user.id, f"Пожалуйста, введите текст задачи:")
        Connection.setUserState(message.from_user.username, STATE_ACTIONTEXT)

    def showActionsHandler(self, message):
        username = message.from_user.username
        telegramid = message.from_user.id
        # Check user first
        if (not self.checkUser(username=username)):
            self.sendMessage(id, f'Пользователь не зарегистрирован. Пожалуйста, введите "{CMD_START}"')
            return False
        # Get all active actions
        actions = Connection.getActions(username=username, active=True)
        for action in actions:
            self.sendMessage(telegramid, f'Action {action["title"]}: {action["text"]}')
        # TODO: show actions as buttons

    def completeActionHandler(self, message):
        pass

    def cancelActionHandler(self, message):
        pass