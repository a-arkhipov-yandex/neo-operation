from os import getenv
from dotenv import load_dotenv
import telebot
from telebot import types
import re
from datetime import datetime as dt
from datetime import timedelta
from zoneinfo import ZoneInfo
from log_lib import *
from db_lib import *

ENV_BOTTOKEN = 'BOTTOKEN'
ENV_BOTTOKENTEST = 'BOTTOKENTEST'

ENV_TESTDB = 'TESTDB'
ENV_TESTBOT = 'TESTBOT'

ENV_DEFAULTREMINDERTIME = "DEFAULTREMINDERTIME"

VERSION = '0.2'

TITLETEXT_SEPARATOR = '@@@'

CMD_START = '/start'
CMD_HELP = '/help'
CMD_NEWACTION = '/newaction'
CMD_SHOWACTIONS = '/showactions'
CMD_COMPLETEACTION = '/completeaction'
CMD_CANCELACTION = '/cancelaction'

CALLBACK_ACTION_TAG = 'actionId:'
CALLBACK_ACTIONCOMPLETE_TAG = 'completeActionId:'
CALLBACK_ACTIONCANCEL_TAG = 'cancelActionId:'
CALLBACK_ACTIONREMINDERSET_TAG = 'reminderSetActionId:'
CALLBACK_ACTIONREMINDERSTOP_TAG = 'reminderStopActionId:'
CALLBACK_ACTIONTITLECHANGE_TAG = 'titleChangeActionId:'

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

def getDefaultReminderTime():
    load_dotenv()
    defaultReminder = getenv(ENV_DEFAULTREMINDERTIME)
    if (not defaultReminder):
        defaultReminder == "09:00"
    return defaultReminder

def getCurrentDateTime():
    tzinfo=ZoneInfo('Europe/Moscow')
    startTime = dt.now(tzinfo).strftime("%d-%m-%Y %H:%M:%S")
    return startTime

#=====================
# Bot class
#---------------------
class NeoOperationBot:
    __bot = None

    def registerHandlers(self):
        NeoOperationBot.__bot.register_message_handler(self.messageHandler)
        NeoOperationBot.__bot.register_callback_query_handler(
            self.actionButtonHandler,
            func=lambda message: re.match(fr'^{CALLBACK_ACTION_TAG}\d+$', message.data)
        )
        NeoOperationBot.__bot.register_callback_query_handler(
            self.completeActionHandler,
            func=lambda message: re.match(fr'^{CALLBACK_ACTIONCOMPLETE_TAG}\d+$', message.data)
        )
        NeoOperationBot.__bot.register_callback_query_handler(
            self.cancelActionHandler,
            func=lambda message: re.match(fr'^{CALLBACK_ACTIONCANCEL_TAG}\d+$', message.data)
        )
        NeoOperationBot.__bot.register_callback_query_handler(
            self.reminderSetActionHandler,
            func=lambda message: re.match(fr'^{CALLBACK_ACTIONREMINDERSET_TAG}\d+$', message.data)
        )
        NeoOperationBot.__bot.register_callback_query_handler(
            self.reminderStopActionHandler,
            func=lambda message: re.match(fr'^{CALLBACK_ACTIONREMINDERSTOP_TAG}\d+$', message.data)
        )
        NeoOperationBot.__bot.register_callback_query_handler(
            self.titleChangeActionHandler,
            func=lambda message: re.match(fr'^{CALLBACK_ACTIONTITLECHANGE_TAG}\d+$', message.data)
        )

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
        self.registerHandlers()

    def isInitialized():
        return (NeoOperationBot.__bot != None)

    def getBot(self):
        return self.__bot

    # Init bot
    def __init__(self):
        self.forwardChache = {}
        self.defaultReminderTime = getDefaultReminderTime()

        # Check if bot is initialized
        if (not NeoOperationBot.isInitialized()):
            NeoOperationBot.initBot(self)
        self.bot = NeoOperationBot.__bot

    def setForwardCache(self, username, text):
        if (not NeoOperationBot.isInitialized()):
            log(f'Bot is not initialized - set cache', LOG_ERROR)
            return
        self.forwardChache[username] = text
        log(f'Set forward cache for user {username}: {text}')

    def clearForwardCache(self, username):
        if (not NeoOperationBot.isInitialized()):
            log(f'Bot is not initialized - clear cache', LOG_ERROR)
            return
        if (self.forwardChache.get(username)):
            self.forwardChache[username] = ''
            log(f'Clear forward cache for user {username}')

    def getForwardCache(self, username):
        if (not NeoOperationBot.isInitialized()):
            log(f'Bot is not initialized - get cache', LOG_ERROR)
            return
        return self.forwardChache.get(username)

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
    def generateActionTitle(self, fromTxt=None):
        datetimenow = getCurrentDateTime()
        additional = ''
        if (fromTxt):
            additional = f'от @{fromTxt} '
        return f"Задача {additional}- {datetimenow}"

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

    # Check existance of action and it belongs to user
    def checkUserAndAction(self, username, actionInfo):
        if (actionInfo['username'] == username):
            return True
        return False

    # Send message to user
    def sendMessage(self, telegramid, text):
        if (NeoOperationBot.isInitialized()):
            NeoOperationBot.__bot.send_message(telegramid, text)

    # Get forward nessage
    def getFromTxt(self, message):
        fromTxt = None
        # Check fromard message
        if (message.forward_origin):
            fromTxt = message.forward_origin.sender_user.username
        return fromTxt

    def getTitleAndText(self, fromTxtTitle, fromTxtUser, txt):
        title = ''
        text = ''
        tmp = txt.split(TITLETEXT_SEPARATOR)
        if (len(tmp) != 2):
            title = self.generateActionTitle(fromTxtTitle)
            text = f'@{fromTxtUser}: {txt}'
        else:
            title = tmp[0]
            text = f'@{fromTxtUser}: {tmp[1]}'
        return (title, text)

    def replyHandler(self, message):
        # Check current user state
        username = message.from_user.username
        id = message.from_user.id
        if (not self.checkUser(username=username)):
            self.sendMessage(id, f'Пользователь не зарегистрирован. Пожалуйста, введите "{CMD_START}"')
            return False
        
        title = ''
        text = ''
        fromTxt = self.getFromTxt(message)
        textByUser = self.getForwardCache(username=username)
        self.clearForwardCache(username=username)
        if (fromTxt and (textByUser and len(textByUser))): # there is text by user
            text = message.text
            (title, text2) = self.getTitleAndText(fromTxtTitle=fromTxt, fromTxtUser=username, txt=textByUser)
            text = f"@{fromTxt}: {text}\n{text2}"
        else:
            if (not fromTxt):
                fromTxt = username
            textByUser = message.text
            (title, text) = self.getTitleAndText(fromTxtTitle=fromTxt, fromTxtUser=fromTxt, txt=textByUser)
            text = f'{text}'
        Connection.addAction(username=username, title=title, text=text, fromTxt=fromTxt)
        Connection.clearUserState(username=username)
        self.sendMessage(id, f'Новая задача "{title}" создана успешно.')
        return True

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
        elif re.match('^/ф\s+\S+', text):
            self.preForwardHandle(message)
        else:
            self.sendMessage(telegramid, "Неизвестная команда.")
            self.sendMessage(telegramid, self.getHelpMessage(message.from_user.username))

    # Handler for text along with fowrarded message
    def preForwardHandle(self, message):
        text = message.text[3:] # Remove '/ф '
        username = message.from_user.username
        self.setForwardCache(username, text)

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

    # Get reminder description
    def getReminderText(self, actionInfo):
        text = '''
Не установлено
        '''
        if (actionInfo['reminder']):
            text = f'''
Установлено на "{actionInfo["reminder"]}"
            '''
        return text

    # Action menu
    def getActionMenu(self, actionId):
        # Complete
        key1 = types.InlineKeyboardButton(
            text=f'Отметить задачу сделанной',
            callback_data=f'{CALLBACK_ACTIONCOMPLETE_TAG}{actionId}'
        )
        # Cancel
        key2 = types.InlineKeyboardButton(
            text=f'Отменить задачу',
            callback_data=f'{CALLBACK_ACTIONCANCEL_TAG}{actionId}'
        )
        # Set reminder
        key3 = types.InlineKeyboardButton(
            text=f'Установить напоминание на следующее утро',
            callback_data=f'{CALLBACK_ACTIONREMINDERSET_TAG}{actionId}'
        )
        # Stop Reminder
        key4 = types.InlineKeyboardButton(
            text=f'Не напоминать больше',
            callback_data=f'{CALLBACK_ACTIONREMINDERSTOP_TAG}{actionId}'
        )
        # Change title
        key5 = types.InlineKeyboardButton(
            text=f'Изменить заголовок задачи',
            callback_data=f'{CALLBACK_ACTIONTITLECHANGE_TAG}{actionId}'
        )

        keyboard = types.InlineKeyboardMarkup(); # keyboard
        keyboard.add(key1)
        keyboard.add(key2)
        keyboard.add(key3)
        keyboard.add(key4)
        keyboard.add(key5)
        return keyboard

    # Extract action info from callback data
    # Returns:
    #   None - error during extraction
    #   actionId - action id
    def extractActionInfo(self, username, data):
        fName = self.extractActionInfo.__name__
        try:
            actionId = int(data.split(':')[1])
        except:
            log(f'{fName}: Incorrect actionId provided: {data}')
            return None
        actionInfo = Connection.getActionInfo(username=username, actionId=actionId)
        if (not dbFound(actionInfo)):
            log(f'{fName}: Cannot find actionId provided: {username} - {actionId}',LOG_ERROR)
            return None
        return actionInfo

    def actionButtonHandler(self, message):
        fName = self.actionButtonHandler.__name__
        telegramid = message.from_user.id
        username = message.from_user.username
        data = message.data
        actionInfo = self.extractActionInfo(username=username, data=data)
        if (not actionInfo):
            self.sendMessage(telegramid, 'Ошибка обработки сообщения. Попробуйте еще раз.')
            return
        actionId = actionInfo['id']
        reminder = self.getReminderText(actionInfo)
        text = f'''
Задача:
{actionInfo["title"]}
Описание:
{actionInfo["text"]}
Напоминание: {reminder}

        '''
        self.sendMessage(message.from_user.id, text)
        keyboard = self.getActionMenu(actionId=actionId)
        self.bot.send_message(telegramid, text='Выберите действие с задачей:', reply_markup=keyboard)

    def newActionHandler(self, message):
        fName = self.newActionHandler.__name__
        if (not NeoOperationBot.isInitialized()):
            log(f'{fName}: Bot is not initialized', LOG_ERROR)
            return
        self.sendMessage(message.from_user.id, f"Пожалуйста, введите заголовок и текст задачи (разделитель '!!!'):")
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
        keyboard = types.InlineKeyboardMarkup(); # keyboard
        question = 'Выберите задачу для обработки:'
        if (len(actions) == 0):
            # No active actions
            self.sendMessage(telegramid, f'У вас нет активных задач. Создайте при помощи {CMD_NEWACTION}')
        else:
            for action in actions:
                key = types.InlineKeyboardButton(
                    text=f'{action["title"]}',
                    callback_data=f'{CALLBACK_ACTION_TAG}{action["id"]}'
                )
                keyboard.add(key)
            self.bot.send_message(telegramid, text=question, reply_markup=keyboard)

    def completeActionHandler(self, message):
        username = message.from_user.username
        telegramid = message.from_user.id
        data = message.data
        actionInfo = self.extractActionInfo(username=username, data=data)
        if (not actionInfo):
            self.sendMessage(telegramid, 'Ошибка обработки сообщения. Попробуйте еще раз.')
            return
        actionId = actionInfo['id']
        # Complete action
        ret = Connection.completeAction(actionId=actionId, username=username)
        if (ret):
            self.sendMessage(telegramid, f'Задача "{actionInfo["title"]}" помечена выполненой. Вы - молодец!')
        else:
            self.sendMessage(telegramid, f'Произошла ошибка. Попробуйте позже.')

    def cancelActionHandler(self, message):
        telegramid = message.from_user.id
        username = message.from_user.username
        data = message.data
        actionInfo = self.extractActionInfo(username=username, data=data)
        if (not actionInfo):
            self.sendMessage(telegramid, 'Ошибка обработки сообщения. Попробуйте еще раз.')
            return
        actionId = actionInfo['id']
        ret = Connection.cancelAction(actionId=actionId, username=username)
        if (ret):
            self.sendMessage(telegramid, f'Задача "{actionInfo["title"]}" отменена.')
        else:
            self.sendMessage(telegramid, f'Произошла ошибка. Попробуйте позже.')

    def reminderSetActionHandler(self, message):
        telegramid = message.from_user.id
        username = message.from_user.username
        data = message.data
        actionInfo = self.extractActionInfo(username=username, data=data)
        if (not actionInfo):
            self.sendMessage(telegramid, 'Ошибка обработки сообщения. Попробуйте еще раз.')
            return
        actionId = actionInfo['id']
        reminder = self.getNextReminder()
        ret = Connection.setReminder(username=username, actionId=actionId, reminder=reminder)
        if (ret):
            rTxt = self.getTimeDateTxt(reminder)
            self.sendMessage(telegramid, f'Напоминание для задачи {actionInfo["title"]} установлено на {rTxt}.')
        else:
            self.sendMessage(telegramid, 'Произошла ошибка. Попробуйте позже.')

    def reminderStopActionHandler(self, message):
        telegramid = message.from_user.id
        username = message.from_user.username
        data = message.data
        actionInfo = self.extractActionInfo(username=username, data=data)
        if (not actionInfo):
            self.sendMessage(telegramid, 'Ошибка обработки сообщения. Попробуйте еще раз.')
            return
        actionId = actionInfo['id']
        ret = Connection.clearReminder(username=username, actionId=actionId)
        if (ret):
            self.sendMessage(telegramid, f'Напоминание для задачи {actionInfo["title"]} удалено.')
        else:
            self.sendMessage(telegramid, 'Произошла ошибка. Попробуйте позже.')

    def titleChangeActionHandler(self, message):
        telegramid = message.from_user.id
        username = message.from_user.username
        data = message.data
        actionInfo = self.extractActionInfo(username=username, data=data)
        if (not actionInfo):
            self.sendMessage(telegramid, 'Ошибка обработки сообщения. Попробуйте еще раз.')
            return
        actionId = actionInfo['id']
        # TODO: implement it
        self.sendMessage(telegramid, f'Title Change action not implemented {message.data}')

    # Get next reminder datetime
    # Returns: datetime object with new reminder
    def getNextReminder(self, daysToDelay=1):
        # Get current date
        today = dt.now()
        # Add one day
        oneDay = timedelta(days=daysToDelay)
        tomorrow = today + oneDay
        # Set time to default time
        (hours, minutes) = self.defaultReminderTime.split(':')
        hours = int(hours)
        minutes = int(minutes)
        newTomorrow = dt(year=tomorrow.year,month=tomorrow.month,day=tomorrow.day,
                         hour=hours,minute=minutes,second=0)
        return newTomorrow

    def getTimeDateTxt(self, reminder):
        return reminder.strftime("%d-%m-%Y %H:%M:%S")
