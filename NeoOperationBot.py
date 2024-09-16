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

VERSION = '0.3'

TITLETEXT_SEPARATOR = '@@@'

CMD_START = '/start'
CMD_HELP = '/help'
CMD_NEWACTION = '/newaction'
CMD_SHOWACTIONS = '/showactions'
CMD_COMPLETEACTION = '/completeaction'
CMD_CANCELACTION = '/cancelaction'
CMD_SHOWREMINDERS = '/showreminders'

CALLBACK_ACTION_TAG = 'actionId:'
CALLBACK_ACTIONCOMPLETE_TAG = 'completeActionId:'
CALLBACK_ACTIONCANCEL_TAG = 'cancelActionId:'
CALLBACK_ACTIONREMINDERSET_TAG = 'reminderSetActionId:'
CALLBACK_ACTIONREMINDERSTOP_TAG = 'reminderStopActionId:'
CALLBACK_ACTIONTITLECHANGE_TAG = 'titleChangeTitle:'

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

# Get next reminder datetime
# Returns: datetime object with new reminder
def getNextReminder(daysToDelay=1):
    # Get current date
    today = dt.now()
    # Add one day
    oneDay = timedelta(days=daysToDelay)
    tomorrow = today + oneDay
    # Set time to default time
    (hours, minutes) = NeoOperationBot.defaultReminderTime.split(':')
    hours = int(hours)
    minutes = int(minutes)
    newTomorrow = dt(year=tomorrow.year,month=tomorrow.month,day=tomorrow.day,
                        hour=hours,minute=minutes,second=0)
    return newTomorrow

# Action menu
# If reminder=True - hide buttons after press
def getActionMenu(actionId, reminder=False):
    # Complete
    key1 = types.InlineKeyboardButton(
        text=f'\U00002705 Отметить задачу сделанной',
        callback_data=f'{CALLBACK_ACTIONCOMPLETE_TAG}{actionId}'
    )
    # Cancel
    key2 = types.InlineKeyboardButton(
        text=f'\U0000274C Отменить задачу',
        callback_data=f'{CALLBACK_ACTIONCANCEL_TAG}{actionId}'
    )
    # Set reminder
    key3 = types.InlineKeyboardButton(
        text=f'\U0001F514 Установить напоминание на следующее утро',
        callback_data=f'{CALLBACK_ACTIONREMINDERSET_TAG}{actionId}'
    )
    # Stop Reminder
    key4 = types.InlineKeyboardButton(
        text=f'\U0001F515 Не напоминать больше',
        callback_data=f'{CALLBACK_ACTIONREMINDERSTOP_TAG}{actionId}'
    )
    if (not reminder):
        # Change title
        key5 = types.InlineKeyboardButton(
            text=f'\U0001F58B Изменить заголовок задачи',
            callback_data=f'{CALLBACK_ACTIONTITLECHANGE_TAG}{actionId}'
        )

    keyboard = types.InlineKeyboardMarkup(); # keyboard
    keyboard.add(key1)
    keyboard.add(key2)
    keyboard.add(key3)
    keyboard.add(key4)
    if (not reminder):
        keyboard.add(key5)
    return keyboard

    # Get reminder description
def getReminderText(actionInfo):
    text = '''
\U0001F6AB Не установлено
    '''
    if (actionInfo['reminder']):
        text = f'''
\U000023F0 Установлено на "{actionInfo["reminder"]}"
        '''
    return text

def getActionInfoText(actionInfo):
    reminder = getReminderText(actionInfo)
    text = f'''
\U0001F3AF Задача: {actionInfo["title"]}
\U0001F4DC Описание:
{actionInfo["text"]}
\U0000231B Напоминание: {reminder}
    '''
    return text

#=====================
# Bot class
#---------------------
class NeoOperationBot:
    __bot = None
    defaultReminderTime = None

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
        NeoOperationBot.defaultReminderTime = getDefaultReminderTime()

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
        fName = self.replyHandler.__name__
        # Check current user state
        username = message.from_user.username
        id = message.from_user.id
        if (not self.checkUser(username=username)):
            self.sendMessage(id, f'Пользователь не зарегистрирован. Пожалуйста, введите "{CMD_START}"')
            return True
        
        state = Connection.getUserState(username=username)
        if (state == STATE_ACTIONTITLECHANGE):
            # Handle title change here
            newTitle = message.text
            # Get action ID from DB
            userInfo = Connection.getUserInfoByName(username=username)
            actionId = int(userInfo['state_data'])
            actionInfo = Connection.getActionInfo(username=username, actionId=actionId)
            if (not dbFound(actionInfo)):
                log(f'{fName}: Cannot find action id {actionId} for user {username}')
                self.sendMessage(id, 'Ошибка при изменении заголовка. Попробуйте позже.')
                return True
            # update title
            ret = Connection.udpdateActionTitle(username=username, actionId=actionId, newTitle=newTitle)
            if (not ret):
                log(f'{fName}: Error updating title action {actionId} for user {username}', LOG_ERROR)
                self.sendMessage(id, 'Произошла ошибка - не могу поменять заголовок. Попробуйте позже')
            else:
                log(f'{fName}: Successfully changed action title: action {actionId}, new title {newTitle}')
                self.sendMessage(id, f'Установлен новый заголовок "{newTitle}"')
            # Clear state
            Connection.clearUserState(username=username)
            return True

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
        username = message.from_user.username
        # Clear state
        Connection.clearUserState(username=username)
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
        elif text == CMD_SHOWREMINDERS:
            self.showRemindersHandler(message)
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
    Команды NeoOperation_Bot:
        {CMD_HELP} - вывести помощь по командам (это сообщение)
        {CMD_START} - регистрация нового пользователя
        {CMD_NEWACTION} - создать новую задачу
        {CMD_SHOWACTIONS} - вывести все активные задачи
        {CMD_SHOWREMINDERS} - вывести все задачи с истекшими напоминаниями
        '''
    # Get welcome message
    def getWelcomeMessage(self, userName):
        ret = f'''
        Добро пожаловать, {userName}!
        Это бот "Neo Operation". Версия: {VERSION}
        '''
        return ret

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

    def actionButtonHandler(self, callback:types.CallbackQuery):
        fName = self.actionButtonHandler.__name__
        telegramid = callback.from_user.id
        username = callback.from_user.username
        data = callback.data
        actionInfo = self.extractActionInfo(username=username, data=data)
        if (not actionInfo):
            self.sendMessage(telegramid, 'Ошибка обработки сообщения. Попробуйте еще раз.')
            log(f'{fName}: Cannot get action from data: {data}')
            return
        actionId = actionInfo['id']
        reminderText = getActionInfoText(actionInfo=actionInfo)
        self.sendMessage(callback.from_user.id, reminderText)
        keyboard = getActionMenu(actionId=actionId)
        message_sent = self.bot.send_message(telegramid,
                                             text='Выберите действие с задачей:',
                                             reply_markup=keyboard,
                                             parse_mode='MarkdownV2')
        # Save chat_id and message_id to hide later
        message_id = message_sent.id
        chat_id = telegramid
        Connection.udpdateActionButtons(username=username,actionId=actionId,buttons=f'{message_id}|{chat_id}')


    def newActionHandler(self, message):
        fName = self.newActionHandler.__name__
        if (not NeoOperationBot.isInitialized()):
            log(f'{fName}: Bot is not initialized', LOG_ERROR)
            return
        self.sendMessage(message.from_user.id, f"Пожалуйста, введите заголовок и текст задачи (разделитель '!!!'):")
        Connection.setUserState(message.from_user.username, STATE_ACTIONTEXT)

    def titleChangeTitle(self, message):
        fName = self.titleChangeTitle.__name__
        username = message.from_user.username
        if (not NeoOperationBot.isInitialized()):
            log(f'{fName}: Bot is not initialized', LOG_ERROR)
            return
        self.sendMessage(message.from_user.id, f"Пожалуйста, введите новый заголовок задачи:")
        Connection.setUserState(message.from_user.username, STATE_ACTIONTITLECHANGE)
        ret = Connection.setUserState(username=username, state=STATE_ACTIONTITLECHANGE)
        if (not ret):
            log(f'{fName}: Error savign state {STATE_ACTIONTITLECHANGE} for user {username}')

    def showRemindersHandler(self, message):
        username = message.from_user.username
        telegramid = message.from_user.id
        # Check user first
        if (not self.checkUser(username=username)):
            self.sendMessage(id, f'Пользователь не зарегистрирован. Пожалуйста, введите "{CMD_START}"')
            return False
        # Get all active actions
        actions = Connection.getActionsWithShownExpiredReminders(username=username)
        keyboard = types.InlineKeyboardMarkup(); # keyboard
        question = 'Выберите задачу для обработки:'
        if (len(actions) == 0):
            # No active actions
            self.sendMessage(telegramid, f'У вас нет активных задач с истекшим напоминанием. Создайте при помощи {CMD_NEWACTION}')
        else:
            for action in actions:
                key = types.InlineKeyboardButton(
                    text=f'{action["title"]}',
                    callback_data=f'{CALLBACK_ACTION_TAG}{action["id"]}'
                )
                keyboard.add(key)
            self.bot.send_message(telegramid, text=question, reply_markup=keyboard)

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
                    text=f'\U0001F4DA {action["title"]}',
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
            # Remove keyboard if set
            self.removeActionKeyboard(actionInfo['buttons'])
            Connection.clearActionButtons(username=username,actionId=actionId)
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
            # Remove keyboard if set
            self.removeActionKeyboard(actionInfo['buttons'])
            Connection.clearActionButtons(username=username,actionId=actionId)
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
        reminder = getNextReminder()
        ret = Connection.setReminder(username=username, actionId=actionId, reminder=reminder)
        if (ret):
            rTxt = self.getTimeDateTxt(reminder)
            # Remove keyboard if set
            self.removeActionKeyboard(actionInfo['buttons'])
            Connection.clearActionButtons(username=username,actionId=actionId)
            self.sendMessage(telegramid, f'Напоминание для задачи "{actionInfo["title"]}" установлено на {rTxt}.')
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
            # Remove keyboard if set
            self.removeActionKeyboard(actionInfo['buttons'])
            Connection.clearActionButtons(username=username,actionId=actionId)
            self.sendMessage(telegramid, f'Напоминание для задачи {actionInfo["title"]} удалено.')
        else:
            self.sendMessage(telegramid, 'Произошла ошибка. Попробуйте позже.')

    def removeActionKeyboard(self, keyboardInfo):
        fName = self.removeActionKeyboard.__name__
        if (keyboardInfo):
            res = keyboardInfo.split('|')
            if (len(res) != 2):
                log(f'{fName}: error getting message and chat: {keyboardInfo}', LOG_ERROR)
                return
            message_id = int(res[0])
            chat_id = int(res[1])
            self.bot.delete_message(message_id=message_id, chat_id=chat_id)

    def titleChangeActionHandler(self, message):
        fName = self.titleChangeActionHandler.__name__
        telegramid = message.from_user.id
        username = message.from_user.username
        data = message.data
        actionInfo = self.extractActionInfo(username=username, data=data)
        if (not actionInfo):
            self.sendMessage(telegramid, 'Ошибка обработки сообщения. Попробуйте еще раз.')
            return
        title = actionInfo['title']
        # save user state and data
        ret = Connection.setUserState(username=username, state=STATE_ACTIONTITLECHANGE, data=actionInfo['id'])
        if (not ret):
            log(f'{fName}: Cannot save state {STATE_ACTIONTITLECHANGE} and data {actionInfo["id"]} for {username}')
            self.sendMessage(telegramid=telegramid, text="Ошибка при изменении заголовка задачи. Попробуйте позже.")
        else:
            self.sendMessage(telegramid, f'Введите новый заголовок для задачи {title}:')

    def getTimeDateTxt(self, reminder):
        return reminder.strftime("%d-%m-%Y %H:%M:%S")
