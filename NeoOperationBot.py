from os import getenv
from dotenv import load_dotenv
import telebot
from telebot import types
import re
import requests
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

VERSION = '1.1'

TITLETEXT_SEPARATOR = '@@@'

CMD_START = '/start'
CMD_HELP = '/help'
CMD_NEWACTION = '/newaction'
CMD_SHOWACTIONS = '/showactions'
CMD_COMPLETEACTION = '/completeaction'
CMD_CANCELACTION = '/cancelaction'
CMD_SHOWREMINDERS = '/showreminders'
CMD_SEARCHACTIVE = '/searchactive'
CMD_SEARCHALL = '/searchall'
CMD_EXIT = '/q' # Exist from any states

CALLBACK_ACTION_TAG = 'actionId:'
CALLBACK_ACTIONACTIVATE_TAG = 'activateActionId:'
CALLBACK_ACTIONCOMPLETE_TAG = 'completeActionId:'
CALLBACK_ACTIONCANCEL_TAG = 'cancelActionId:'
CALLBACK_ACTIONREMINDERSET_TAG = 'reminderSetActionId:'
CALLBACK_ACTIONREMINDERSTOP_TAG = 'reminderStopActionId:'
CALLBACK_ACTIONTITLECHANGE_TAG = 'titleChangeTitle:'
CALLBACK_ACTIONHIDEMENU_TAG = 'hideMenu:'
CALLBACK_ACTIONTEXTADD_TAG = 'textAdd:'
CALLBACK_SEARCHACTIVEACTIONS_TAG = 'searchActiveActions:'
CALLBACK_SEARCHALLACTIONS_TAG = 'searchAllActions:'

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
def getNextReminder(hoursToDelay=None, daysToDelay=None):
    # Get current date
    tzinfo=ZoneInfo('Europe/Moscow')
    today = dt.now(tzinfo)
    delay = timedelta()
    reminder = ''
    if (hoursToDelay):
        delay = timedelta(hours=hoursToDelay)
        reminder = today + delay
    elif (daysToDelay):
        delay = timedelta(days=daysToDelay)
        tomorrow = today + delay
        # Set time to default time
        (hours, minutes) = NeoOperationBot.defaultReminderTime.split(':')
        hours = int(hours)
        minutes = int(minutes)
        reminder = dt(year=tomorrow.year,month=tomorrow.month,day=tomorrow.day,
                            hour=hours,minute=minutes,second=0)
    return reminder

# Action menu based on action status
# If reminder=True - hide buttons after press
def getActionMenu(actionId, active=True):
    keyboard = types.InlineKeyboardMarkup() # keyboard
    if (active):
        # Complete
        key1 = types.InlineKeyboardButton(
            text=f'\U00002705 Сделано!',
            callback_data=f'{CALLBACK_ACTIONCOMPLETE_TAG}{actionId}'
        )
        # Cancel
        key2 = types.InlineKeyboardButton(
            text=f'\U0000274C Отменить',
            callback_data=f'{CALLBACK_ACTIONCANCEL_TAG}{actionId}'
        )
        # Set reminder
        key31 = types.InlineKeyboardButton(
            text=f'\U0001F550 На 1 час',
            callback_data=f'{CALLBACK_ACTIONREMINDERSET_TAG}{actionId}:1'
        )
        key32 = types.InlineKeyboardButton(
            text=f'\U0001F552 На 3 часа',
            callback_data=f'{CALLBACK_ACTIONREMINDERSET_TAG}{actionId}:3'
        )
        key33 = types.InlineKeyboardButton(
            text=f'\U000023F0 На завтра',
            callback_data=f'{CALLBACK_ACTIONREMINDERSET_TAG}{actionId}:1d'
        )
        # Stop Reminder
        key4 = types.InlineKeyboardButton(
            text=f'\U0001F515 Не напоминать больше',
            callback_data=f'{CALLBACK_ACTIONREMINDERSTOP_TAG}{actionId}'
        )
        # Change title
        key5 = types.InlineKeyboardButton(
            text=f'\U0001F58B Изменить заголовок',
            callback_data=f'{CALLBACK_ACTIONTITLECHANGE_TAG}{actionId}'
        )
        # Add text to action
        key6 = types.InlineKeyboardButton(
            text=f'\U0001F4DD Добавить текст',
            callback_data=f'{CALLBACK_ACTIONTEXTADD_TAG}{actionId}'
        )
        # Hide menu
        key7 = types.InlineKeyboardButton(
            text=f'\U00002716 Скрыть меню (ничего не делать)',
            callback_data=f'{CALLBACK_ACTIONHIDEMENU_TAG}{actionId}'
        )
        keyboard.row(key1, key2)
        keyboard.row(key31, key32, key33)
        keyboard.row(key4)
        keyboard.row(key5, key6)
        keyboard.row(key7)
    else:
        # Reactivate
        key1 = types.InlineKeyboardButton(
            text=f'\U0001F4A5 Сделать активной',
            callback_data=f'{CALLBACK_ACTIONACTIVATE_TAG}{actionId}'
        )
        # Change title
        key2 = types.InlineKeyboardButton(
            text=f'\U0001F58B Изменить заголовок',
            callback_data=f'{CALLBACK_ACTIONTITLECHANGE_TAG}{actionId}'
        )
        # Add text to action
        key3 = types.InlineKeyboardButton(
            text=f'\U0001F4DD Добавить текст',
            callback_data=f'{CALLBACK_ACTIONTEXTADD_TAG}{actionId}'
        )
        # Hide menu
        key4 = types.InlineKeyboardButton(
            text=f'\U00002716 Скрыть меню (ничего не делать)',
            callback_data=f'{CALLBACK_ACTIONHIDEMENU_TAG}{actionId}'
        )
        keyboard.row(key1)
        keyboard.row(key2, key3)
        keyboard.row(key4)
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

def getActionStatusText(actionInfo):
    statusTxt = 'Активная \U0001F4A5'
    status = actionInfo['status']
    if (status == ACTION_COMPLETED):
        statusTxt = 'Выполнена \U00002705'
    if (status == ACTION_CANCELLED):
        statusTxt = 'Отменена \U0000274C'
    return statusTxt

def getActionInfoText(actionInfo):
    reminder = getReminderText(actionInfo=actionInfo)
    status = getActionStatusText(actionInfo=actionInfo)
    text = f'''
\U0001F3AF Задача: {actionInfo["title"]}
\U00002734 Статус: {status}
\U0001F4DC Описание:
{actionInfo["text"]}
\U0000231B Напоминание: {reminder}
    '''
    return text

def showActionMenu(bot:telebot.TeleBot, actionInfo, telegramid, addText=''):
    username = actionInfo['username']
    actionId = actionInfo['id']
    # Send action info
    actionInfoText = addText + getActionInfoText(actionInfo=actionInfo)
    actionInfoMessage = bot.send_message(telegramid, actionInfoText) # Save message ID
    keyboard = getActionMenu(actionId=actionId, active=(actionInfo['status'] == ACTION_ACTIVE))
    message_sent = bot.send_message(telegramid,
                                            text='Выберите действие с задачей:',
                                            reply_markup=keyboard,
                                            parse_mode='MarkdownV2')
    actionInfoMessageId = actionInfoMessage.id
    # Save chat_id and message_id to hide later
    message_id = message_sent.id
    chat_id = telegramid
    Connection.udpdateActionButtons(username=username,actionId=actionId,buttons=f'{message_id}|{chat_id}|{actionInfoMessageId}')

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
            self.activateActionHandler,
            func=lambda message: re.match(fr'^{CALLBACK_ACTIONACTIVATE_TAG}\d+$', message.data)
        )
        NeoOperationBot.__bot.register_callback_query_handler(
            self.cancelActionHandler,
            func=lambda message: re.match(fr'^{CALLBACK_ACTIONCANCEL_TAG}\d+$', message.data)
        )
        NeoOperationBot.__bot.register_callback_query_handler(
            self.reminderSetActionHandler,
            func=lambda message: re.match(fr'^{CALLBACK_ACTIONREMINDERSET_TAG}\d+:\S+$', message.data)
        )
        NeoOperationBot.__bot.register_callback_query_handler(
            self.reminderStopActionHandler,
            func=lambda message: re.match(fr'^{CALLBACK_ACTIONREMINDERSTOP_TAG}\d+$', message.data)
        )
        NeoOperationBot.__bot.register_callback_query_handler(
            self.titleChangeActionHandler,
            func=lambda message: re.match(fr'^{CALLBACK_ACTIONTITLECHANGE_TAG}\d+$', message.data)
        )
        NeoOperationBot.__bot.register_callback_query_handler(
            self.hideMenuHandler,
            func=lambda message: re.match(fr'^{CALLBACK_ACTIONHIDEMENU_TAG}\d+$', message.data)
        )
        NeoOperationBot.__bot.register_callback_query_handler(
            self.textAddHandler,
            func=lambda message: re.match(fr'^{CALLBACK_ACTIONTEXTADD_TAG}\d+$', message.data)
        )
        NeoOperationBot.__bot.register_callback_query_handler(
            self.cmdSearchActionsHandler,
            func=lambda message: re.match(fr'^{CALLBACK_SEARCHACTIVEACTIONS_TAG}\d+$', message.data)
        )
        NeoOperationBot.__bot.register_callback_query_handler(
            self.cmdSearchActionsHandler,
            func=lambda message: re.match(fr'^{CALLBACK_SEARCHALLACTIONS_TAG}\d+$', message.data)
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
        log(f'Starting bot...')
        while(True):
            try:
                self.bot.infinity_polling()
            except KeyboardInterrupt:
                log('Exiting by user request')
                break
            except requests.exceptions.ReadTimeout as error:
                log(f'startBot: exception: {error}', LOG_ERROR)

    # Get default title
    def generateActionTitle(self, fromTxt=None):
        datetimenow = getCurrentDateTime()
        additional = ''
        if (fromTxt):
            additional = f'от @{fromTxt} '
        return f"Задача {additional}- {datetimenow}"

    # Message handler
    def messageHandler(self, message:types.Message):
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
        if (not dbLibCheckUserName(username)):
            return False
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
    # Returns: Message ID
    def sendMessage(self, telegramid, text):
        if (NeoOperationBot.isInitialized()):
            ret = NeoOperationBot.__bot.send_message(telegramid, text)
            return ret.message_id
        return None

    # Get forward nessage
    def getFromTxt(self, message:types.Message):
        fromTxt = None
        # Check fromard message
        if (message.forward_origin):
            try:
                fromTxt = message.forward_origin.sender_user.username
            except:
                fromTxt = "!!!anonymus"
        return fromTxt

    def getTitleAndText(self, fromTxtTitle, fromTxtUser, txt:str):
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

    def replyHandler(self, message:types.Message):
        fName = self.replyHandler.__name__
        # Check current user state
        if (not self.checkUser(username=username)):
            log(f'{fName}: userCheck error - {username}', LOG_WARNING)
            self.sendMessage(id, f'Пользователь не зарегистрирован. Пожалуйста, введите "{CMD_START}"')
            return True
        username = message.from_user.username
        id = message.from_user.id
        state = Connection.getUserState(username=username)
        if (state == STATE_ACTIONTITLECHANGE):
            # Handle title change here
            newTitle = message.text
            # Get action ID from DB
            userInfo = Connection.getUserInfoByName(username=username)
            actionId = int(userInfo['state_data'])
            actionInfo = Connection.getActionInfo(username=username, actionId=actionId)
            if (not dbFound(actionInfo)):
                log(f'{fName}: Cannot find action id {actionId} for user {username}', LOG_ERROR)
                self.sendMessage(id, 'Ошибка при изменении заголовка. Попробуйте позже.')
                return True
            # update title
            ret = Connection.udpdateActionTitle(username=username, actionId=actionId, newTitle=newTitle)
            if (not ret):
                log(f'{fName}: Error updating title action {actionId} for user {username}', LOG_ERROR)
                self.sendMessage(id, 'Произошла ошибка - не могу поменять заголовок. Попробуйте позже.')
            else:
                log(f'{fName}: Successfully changed action title: action {actionId}, new title {newTitle}')
                self.sendMessage(id, f'Установлен новый заголовок "{newTitle}"')
            # Clear state
            Connection.clearUserState(username=username)
            return True
        elif (state == STATE_ACTIONTEXTADD):
            # Handle add text here
            # Get timestamp
            curDate = getCurrentDateTime()
            addText = f'{curDate}: {message.text}'
            # Get action ID from DB
            userInfo = Connection.getUserInfoByName(username=username)
            if (not dbFound(userInfo)):
                log(f'{fName}: Cannot find action id {actionId} for user {username}',LOG_ERROR)
                self.sendMessage(id, 'Ошибка при изменении заголовка. Попробуйте позже.')
                return True
            actionId = int(userInfo['state_data'])
            actionInfo = Connection.getActionInfo(username=username, actionId=actionId)
            if (not dbFound(actionInfo)):
                log(f'{fName}: Cannot find action id {actionId} for user {username}', LOG_ERROR)
                self.sendMessage(id, 'Ошибка при изменении заголовка. Попробуйте позже.')
                return True
            # update title
            ret = Connection.udpdateActionText(username=username, actionId=actionId, addText=addText)
            if (not ret):
                log(f'{fName}: Error updating title action {actionId} for user {username}', LOG_ERROR)
                self.sendMessage(id, 'Произошла ошибка - не могу добавить текст в задачу. Попробуйте позже')
            else:
                log(f'{fName}: Successfully added text: action {actionId}, addText {addText}')
                self.sendMessage(id, f'Добавление текста в задачу прошло успешно')
            # Clear state
            Connection.clearUserState(username=username)
            return True
        elif (state in [STATE_SEARCHACTIVEACTIONS, STATE_SEARCHALLACTIONS]):
            self.searchActionsHandler(message, state)
            return True
        # Add new action here
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
        actionId = Connection.addAction(username=username, title=title, text=text, fromTxt=fromTxt)
        if (not actionId):
            log(f'{fName}: Cannot create action for {username}', LOG_ERROR)
            self.sendMessage(telegramid=id, text='Ошибка при создании задачи. Попробуйте позже')
            return True
        self.sendMessage(id, f'Новая задача "{title}" создана успешно.')
        Connection.clearUserState(username=username)
        # Add reminder to next day
        actionInfo = Connection.getActionInfo(username=username, actionId=actionId)
        self.setReminder(actionInfo=actionInfo)
        return True

    def cmdStartHandler(self, message:types.Message):
        fName = self.cmdStartHandler.__name__
        username = message.from_user.username
        telegramid = message.from_user.id
        # Check if user exists
        if (not self.checkUser(username=username)):
            # Register new user if not registered yet
            userId = Connection.addUser(username=username, telegramid=telegramid)
            if (not userId):
                log(f'{fName}: Cannot register user {username}', LOG_ERROR)
                self.sendMessage(telegramid, 'Ошибка при регистоации пользователя. Попробуйте позже.')
            # Send welcome message
            self.sendMessage(telegramid, 'Регистрация пользователя прошла успешно.')
            self.cmdHelpHandler(message)
        else:
            # Show help message
            self.cmdHelpHandler(message)

    def cmdHandler(self, message:types.Message):
        fName = self.cmdHandler.__name__
        telegramid = message.from_user.id
        username = message.from_user.username
        if (not self.checkUser(username=username)):
            log(f'{fName}: userCheck error - {username}', LOG_WARNING)
            self.sendMessage(telegramid, f'Пользователь не зарегистрирован. Пожалуйста, введите "{CMD_START}"')
            return
        # Clear state
        Connection.clearUserState(username=username)
        text = message.text.lower()
        if text == CMD_HELP:
            self.cmdHelpHandler(message)
        elif text == CMD_EXIT:
            self.cmdQuitHandler(message)
        elif text == CMD_START:
            self.cmdStartHandler(message)
        elif text == CMD_NEWACTION:
            self.cmdNewActionHandler(message)
        elif text == CMD_SHOWACTIONS:
            self.cmdShowActionsHandler(message)
        elif text == CMD_SHOWREMINDERS:
            self.cmdShowRemindersHandler(message)
        elif text == CMD_SEARCHACTIVE:
            self.cmdSearchActionsHandler(message, STATE_SEARCHACTIVEACTIONS)
        elif text == CMD_SEARCHALL:
            self.cmdSearchActionsHandler(message, STATE_SEARCHALLACTIONS)
        elif re.match(r'^/ф\s+\S+', text):
            self.cmdPreForwardHandle(message)
        else:
            self.sendMessage(telegramid, "Неизвестная команда.")
            self.sendMessage(telegramid, self.getHelpMessage(message.from_user.username))

    # Handler for text along with fowrarded message
    def cmdPreForwardHandle(self, message:types.Message):
        text = message.text[3:] # Remove '/ф '
        username = message.from_user.username
        self.setForwardCache(username, text)

    # /help cmd handler
    def cmdQuitHandler(self, message:types.Message):
        # Clear state for user
        username = message.from_user.username
        Connection.clearUserState(username=username)

    # /help cmd handler
    def cmdHelpHandler(self, message:types.Message):
        self.sendMessage(message.from_user.id, self.getHelpMessage(message.from_user.username))

    # Returns help message
    def getHelpMessage(self, username):
        if (not NeoOperationBot.isInitialized()):
            log(f'Bot is not initialized - cannot start', LOG_ERROR)
            return
        ret = self.getWelcomeMessage(username)
        return ret + f'''
    Команды NeoOperation_Bot:
        {CMD_HELP} - вывести помощь по командам (это сообщение)
        {CMD_START} - регистрация нового пользователя
        {CMD_NEWACTION} - создать новую задачу
        {CMD_SHOWACTIONS} - вывести все активные задачи
        {CMD_SHOWREMINDERS} - вывести все задачи с истекшими напоминаниями
        {CMD_SEARCHACTIVE} - искать в заголовке или тексте активных задач
        {CMD_SEARCHALL} - искать в заголовке или тексте всех задач
        '''
    # Get welcome message
    def getWelcomeMessage(self, userName):
        ret = f'''
        Добро пожаловать, {userName}!
        Это бот "Neo Operation". Версия: {VERSION}
        '''
        return ret

    # Extract reminder info from callback data
    # Returns:
    #   None - error during extraction
    #   reminderTimeDate
    def extractReminder(self, data:str):
        fName = self.extractReminder.__name__
        dataPayload = data.split(':')
        if (len(dataPayload) != 3):
            log(f'{fName}: Error during reminder extraction: {data}',LOG_ERROR)
            return None
        reminderTag = dataPayload[2]
        reminder = getNextReminder(daysToDelay=1)
        if (reminderTag == '1'):
                reminder = getNextReminder(hoursToDelay=1)
        elif (reminderTag == '3'):
            reminder = getNextReminder(hoursToDelay=3)
        return reminder

    # Extract action info from callback data
    # Returns:
    #   None - error during extraction
    #   actionInfo - action info
    def extractActionInfo(self, username, data:str):
        fName = self.extractActionInfo.__name__
        dataPayload = data.split(':')
        try:
            actionId = int(dataPayload[1])
        except:
            log(f'{fName}: Incorrect actionId provided: {data}',LOG_ERROR)
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
        if (not self.checkUser(username=username)):
            log(f'{fName}: userCheck error - {username}', LOG_ERROR)
            self.sendMessage(telegramid, f'Пользователь не зарегистрирован. Пожалуйста, введите "{CMD_START}"')
            return
        data = callback.data
        self.bot.answer_callback_query(callback.id)
        actionInfo = self.extractActionInfo(username=username, data=data)
        if (not actionInfo):
            self.sendMessage(telegramid, 'Ошибка обработки сообщения. Попробуйте еще раз.')
            log(f'{fName}: Cannot get action from data: {data}',LOG_ERROR)
            return
        showActionMenu(bot = self.bot, actionInfo=actionInfo,telegramid=telegramid)

    def cmdNewActionHandler(self, message:types.Message):
        fName = self.cmdNewActionHandler.__name__
        if (not NeoOperationBot.isInitialized()):
            log(f'{fName}: Bot is not initialized', LOG_ERROR)
            return
        self.sendMessage(message.from_user.id, f"Пожалуйста, введите заголовок и текст задачи (разделитель '{TITLETEXT_SEPARATOR}'):")
        Connection.setUserState(message.from_user.username, STATE_ACTIONTEXT)

    def cmdShowRemindersHandler(self, callback:types.Message):
        username = callback.from_user.username
        telegramid = callback.from_user.id
        # Get all active actions
        actions = Connection.getActionsWithShownExpiredReminders(username=username)
        if (len(actions) == 0):
            # No active actions
            self.sendMessage(telegramid, f'У вас нет активных задач с истекшим напоминанием. Создайте при помощи {CMD_NEWACTION}')
        else:
            keyboard = types.InlineKeyboardMarkup(); # keyboard
            question = 'Выберите задачу для обработки:'
            for action in actions:
                key = types.InlineKeyboardButton(
                    text=f'{action["title"]}',
                    callback_data=f'{CALLBACK_ACTION_TAG}{action["id"]}'
                )
                keyboard.add(key)
            self.bot.send_message(telegramid, text=question, reply_markup=keyboard)

    def cmdShowActionsHandler(self, message:types.Message):
        username = message.from_user.username
        telegramid = message.from_user.id
        # Get all active actions
        actions = Connection.getActions(username=username, active=True)
        if (len(actions) == 0):
            # No active actions
            self.sendMessage(telegramid, f'У вас нет активных задач. Создайте при помощи {CMD_NEWACTION}')
        else:
            question = 'Выберите задачу для обработки:'
            keyboard = self.getActionsKeyboard(actions)
            self.bot.send_message(telegramid, text=question, reply_markup=keyboard)

    def searchActionsHandler(self, message:types.Message, state):
        fName = self.searchActionsHandler.__name__
        username = message.from_user.username
        telegramid = message.from_user.id
        if (not self.checkUser(username=username)):
            log(f'{fName}: userCheck error - {username}', LOG_ERROR)
            self.sendMessage(telegramid, f'Пользователь не зарегистрирован. Пожалуйста, введите "{CMD_START}"')
            return
        text_to_search = message.text
        log(f'{fName} invoked with params state={state}, text={text_to_search}',LOG_DEBUG)
        # Check state
        if (not dbLibCheckUserState(state=state)):
            log(f'{fName}: Incorrect state provided: {state}', LOG_ERROR)
            self.sendMessage(telegramid=telegramid, text='Произошла ошибка. Попробуйте позже.')
            return
        status = ACTION_ACTIVE
        if (state == STATE_SEARCHALLACTIONS):
            status = None
        # Get all active actions
        actions = Connection.searchActions(textToSearch=text_to_search, username=username, status=status)
        if (len(actions) == 0):
            # No active actions
            self.sendMessage(telegramid, f'Не найдено ни одной задачи. Попробуйте изменить условие поиска.')
        else:
            question = 'Список задач:'
            keyboard = self.getActionsKeyboard(actions=actions)
            self.bot.send_message(telegramid, text=question, reply_markup=keyboard)

    def getActionsKeyboard(self, actions):
        keyboard = types.InlineKeyboardMarkup(); # keyboard
        for action in actions:
            remTxt = ''
            if (action['reminder']):
                remTxt = ' \U0001F514'
            key = types.InlineKeyboardButton(
                text=f'\U0001F4DA {action["title"]}{remTxt}',
                callback_data=f'{CALLBACK_ACTION_TAG}{action["id"]}'
            )
            keyboard.add(key)
        return keyboard

    def activateActionHandler(self, callback:types.CallbackQuery):
        fName = self.activateActionHandler.__name__
        username = callback.from_user.username
        telegramid = callback.from_user.id
        if (not self.checkUser(username=username)):
            log(f'{fName}: userCheck error - {username}', LOG_ERROR)
            self.sendMessage(telegramid, f'Пользователь не зарегистрирован. Пожалуйста, введите "{CMD_START}"')
            return
        data = callback.data
        self.bot.answer_callback_query(callback.id)
        actionInfo = self.extractActionInfo(username=username, data=data)
        if (not actionInfo):
            log(f'{fName}: Cannot extract action from callback data {data}',LOG_ERROR)
            self.sendMessage(telegramid, 'Ошибка обработки сообщения. Попробуйте еще раз.')
            return
        actionId = actionInfo['id']
        # Complete action
        ret = Connection.activateAction(actionId=actionId, username=username)
        if (ret):
            # Remove keyboard if set
            self.removeActionKeyboard(actionInfo['buttons'])
            Connection.clearActionButtons(username=username,actionId=actionId)
            log(f'{fName}: Action {actionId} activated successfully')
            self.sendMessage(telegramid, f'Задача "{actionInfo["title"]}" реактивирована.')
        else:
            log(f'{fName}: Cannot activate {actionId} action', LOG_ERROR)
            self.sendMessage(telegramid, f'Произошла ошибка. Попробуйте позже.')

    def completeActionHandler(self, callback:types.CallbackQuery):
        fName = self.completeActionHandler.__name__
        username = callback.from_user.username
        telegramid = callback.from_user.id
        if (not self.checkUser(username=username)):
            log(f'{fName}: userCheck error - {username}', LOG_ERROR)
            self.sendMessage(telegramid, f'Пользователь не зарегистрирован. Пожалуйста, введите "{CMD_START}"')
            return
        data = callback.data
        self.bot.answer_callback_query(callback.id)
        actionInfo = self.extractActionInfo(username=username, data=data)
        if (not actionInfo):
            log(f'{fName}: Cannot extract action infor from {data}',LOG_ERROR)
            self.sendMessage(telegramid, 'Ошибка обработки сообщения. Попробуйте еще раз.')
            return
        actionId = actionInfo['id']
        # Complete action
        ret = Connection.completeAction(actionId=actionId, username=username)
        if (ret):
            # Remove keyboard if set
            self.removeActionKeyboard(actionInfo['buttons'])
            Connection.clearActionButtons(username=username,actionId=actionId)
            log(f'{fName}: Action {actionId} has been completed')
            self.sendMessage(telegramid, f'Задача "{actionInfo["title"]}" помечена выполненой. Вы - молодец!')
        else:
            log(f'{fName}: Cannot complete {actionId} action', LOG_ERROR)
            self.sendMessage(telegramid, f'Произошла ошибка. Попробуйте позже.')

    def cancelActionHandler(self, callback:types.CallbackQuery):
        fName = self.cancelActionHandler.__name__
        telegramid = callback.from_user.id
        username = callback.from_user.username
        if (not self.checkUser(username=username)):
            log(f'{fName}: userCheck error - {username}', LOG_ERROR)
            self.sendMessage(telegramid, f'Пользователь не зарегистрирован. Пожалуйста, введите "{CMD_START}"')
            return
        data = callback.data
        self.bot.answer_callback_query(callback.id)
        actionInfo = self.extractActionInfo(username=username, data=data)
        if (not actionInfo):
            log(f'{fName}: Cannot extract action info from {data}', LOG_ERROR)
            self.sendMessage(telegramid, 'Ошибка обработки сообщения. Попробуйте еще раз.')
            return
        actionId = actionInfo['id']
        ret = Connection.cancelAction(actionId=actionId, username=username)
        if (ret):
            # Remove keyboard if set
            self.removeActionKeyboard(actionInfo['buttons'])
            Connection.clearActionButtons(username=username,actionId=actionId)
            log(f'{fName}: Action {actionId} has been cancelled successfully')
            self.sendMessage(telegramid, f'Задача "{actionInfo["title"]}" отменена.')
        else:
            log(f'{fName}: Cannot cancel {actionId} action', LOG_ERROR)
            self.sendMessage(telegramid, f'Произошла ошибка. Попробуйте позже.')

    # If reminder is not provider set it to the next day
    # Returns: True/False
    def setReminder(self, actionInfo, reminder=None):
        fName = self.setReminder.__name__
        username = actionInfo['username']
        telegramid = actionInfo['telegramid']
        actionId = actionInfo['id']
        retVal = False
        if (reminder == None):
            reminder = getNextReminder(daysToDelay=1)
        ret = Connection.setReminder(username=username, actionId=actionId, reminder=reminder)
        if (ret):
            rTxt = self.getTimeDateTxt(reminder)
            # Remove keyboard if set
            self.removeActionKeyboard(actionInfo['buttons'])
            Connection.clearActionButtons(username=username,actionId=actionId)
            log(f'{fName}: Reminder for action {actionId} set to {rTxt}')
            self.sendMessage(telegramid, f'Напоминание для задачи "{actionInfo["title"]}" установлено на {rTxt}.')
            retVal = True
        else:
            log(f'{fName}: Error setting reminder {username} - {actionId} - {reminder}', LOG_ERROR)
            self.sendMessage(telegramid, 'Произошла ошибка при установке напоминания. Попробуйте позже.')
        return retVal

    def reminderSetActionHandler(self, callback:types.CallbackQuery):
        fName = self.reminderSetActionHandler.__name__
        telegramid = callback.from_user.id
        username = callback.from_user.username
        if (not self.checkUser(username=username)):
            log(f'{fName}: userCheck error - {username}', LOG_ERROR)
            self.sendMessage(telegramid, f'Пользователь не зарегистрирован. Пожалуйста, введите "{CMD_START}"')
            return
        data = callback.data
        self.bot.answer_callback_query(callback.id)
        actionInfo = self.extractActionInfo(username=username, data=data)
        newReminder = self.extractReminder(data)
        if (not actionInfo or not newReminder):
            log(f'{fName}: Cannot set reminder {data} for user {username}', LOG_ERROR)
            self.sendMessage(telegramid, 'Ошибка обработки сообщения. Попробуйте еще раз.')
            return
        self.setReminder(actionInfo=actionInfo,reminder=newReminder)

    def reminderStopActionHandler(self, callback:types.CallbackQuery):
        fName = self.reminderStopActionHandler.__name__
        telegramid = callback.from_user.id
        username = callback.from_user.username
        if (not self.checkUser(username=username)):
            log(f'{fName}: userCheck error - {username}', LOG_ERROR)
            self.sendMessage(telegramid, f'Пользователь не зарегистрирован. Пожалуйста, введите "{CMD_START}"')
            return
        data = callback.data
        self.bot.answer_callback_query(callback.id)
        actionInfo = self.extractActionInfo(username=username, data=data)
        if (not actionInfo):
            log(f'{fName}: Cannot extract action info from "{data}"', LOG_ERROR)
            self.sendMessage(telegramid, 'Ошибка обработки сообщения. Попробуйте еще раз.')
            return
        actionId = actionInfo['id']
        ret = Connection.clearReminder(username=username, actionId=actionId)
        if (ret):
            # Remove keyboard if set
            self.removeActionKeyboard(actionInfo['buttons'])
            Connection.clearActionButtons(username=username,actionId=actionId)
            log(f'{fName}: Reminder cancelled for {actionId} action')
            self.sendMessage(telegramid, f'Напоминание для задачи {actionInfo["title"]} удалено.')
        else:
            log(f'{fName}: Cannot cancel reminder for action {actionId} and data {data}', LOG_ERROR)
            self.sendMessage(telegramid, 'Произошла ошибка. Попробуйте позже.')

    def removeActionKeyboard(self, keyboardInfo:str):
        print(keyboardInfo)
        fName = self.removeActionKeyboard.__name__
        if (keyboardInfo):
            res = keyboardInfo.split('|')
            if (len(res) != 3):
                log(f'{fName}: error getting messages and chat: {keyboardInfo}', LOG_ERROR)
                return
            message_id = int(res[0])
            chat_id = int(res[1])
            messageInfo_id = int(res[2])
            self.bot.delete_message(message_id=messageInfo_id, chat_id=chat_id)
            self.bot.delete_message(message_id=message_id, chat_id=chat_id)

    def textAddHandler(self, callback:types.CallbackQuery):
        fName = self.textAddHandler.__name__
        telegramid = callback.from_user.id
        username = callback.from_user.username
        if (not self.checkUser(username=username)):
            log(f'{fName}: userCheck error - {username}', LOG_ERROR)
            self.sendMessage(telegramid, f'Пользователь не зарегистрирован. Пожалуйста, введите "{CMD_START}"')
            return
        data = callback.data
        self.bot.answer_callback_query(callback.id)
        actionInfo = self.extractActionInfo(username=username, data=data)
        if (not actionInfo):
            log(f'{fName}: Cannot extract action info from {data}', LOG_ERROR)
            self.sendMessage(telegramid, 'Ошибка обработки сообщения. Попробуйте еще раз.')
            return
        title = actionInfo['title']
        # save user state and data
        ret = Connection.setUserState(username=username, state=STATE_ACTIONTEXTADD, data=actionInfo['id'])
        if (not ret):
            log(f'{fName}: Cannot save state {STATE_ACTIONTEXTADD} and data {actionInfo["id"]} for {username}',LOG_ERROR)
            self.sendMessage(telegramid=telegramid, text="Ошибка при изменении заголовка задачи. Попробуйте позже.")
        else:
            self.removeActionKeyboard(actionInfo['buttons']) # Remove action menu
            self.sendMessage(telegramid, f'Что вы хотите добавить к задаче "{title}" ("/q" отмена):')

    def cmdSearchActionsHandler(self, message:types.Message, state):
        fName = self.cmdSearchActionsHandler.__name__
        telegramid = message.from_user.id
        username = message.from_user.username
        if (not self.checkUser(username=username)):
            log(f'{fName}: userCheck error - {username}', LOG_ERROR)
            self.sendMessage(telegramid, f'Пользователь не зарегистрирован. Пожалуйста, введите "{CMD_START}"')
            return
        # Check state first
        if (not dbLibCheckUserState(state=state)):
            log(f'{fName}: Incorrect state provided: {state}', LOG_ERROR)
            self.sendMessage(telegramid=telegramid, text='Произошла ошибка. Попробуйте позже.')
            return
        ret = Connection.setUserState(username=username, state=state)
        if (not ret):
            log(f'{fName}: Cannot save state {state} for {username}',LOG_ERROR)
            self.sendMessage(telegramid=telegramid, text="Ошибка активации поиска. Попробуйте позже.")
        else:
            self.sendMessage(telegramid, f'Введите текст для поиска в заголовке и/или в описании задачи:')

    def titleChangeActionHandler(self, callback:types.CallbackQuery):
        fName = self.titleChangeActionHandler.__name__
        telegramid = callback.from_user.id
        username = callback.from_user.username
        if (not self.checkUser(username=username)):
            log(f'{fName}: userCheck error - {username}', LOG_ERROR)
            self.sendMessage(telegramid, f'Пользователь не зарегистрирован. Пожалуйста, введите "{CMD_START}"')
            return
        data = callback.data
        self.bot.answer_callback_query(callback.id)
        actionInfo = self.extractActionInfo(username=username, data=data)
        if (not actionInfo):
            log(f'{fName}: Cannot extract user info from "{data}"',LOG_ERROR)
            self.sendMessage(telegramid, 'Ошибка обработки сообщения. Попробуйте еще раз.')
            return
        title = actionInfo['title']
        # save user state and data
        ret = Connection.setUserState(username=username, state=STATE_ACTIONTITLECHANGE, data=actionInfo['id'])
        if (not ret):
            log(f'{fName}: Cannot save state {STATE_ACTIONTITLECHANGE} and data {actionInfo["id"]} for {username}',LOG_ERROR)
            self.sendMessage(telegramid=telegramid, text="Ошибка при изменении заголовка задачи. Попробуйте позже.")
        else:
            self.removeActionKeyboard(actionInfo['buttons']) # Remove action menu
            self.sendMessage(telegramid, f'Введите новый заголовок для задачи "{title}" ("/q" отмена):')

    def hideMenuHandler(self, callback:types.CallbackQuery):
        fName = self.hideMenuHandler.__name__
        telegramid = callback.from_user.id
        username = callback.from_user.username
        if (not self.checkUser(username=username)):
            log(f'{fName}: userCheck error - {username}', LOG_ERROR)
            self.sendMessage(telegramid, f'Пользователь не зарегистрирован. Пожалуйста, введите "{CMD_START}"')
            return
        data = callback.data
        self.bot.answer_callback_query(callback.id)
        actionInfo = self.extractActionInfo(username=username, data=data)
        if (not actionInfo):
            log(f'{fName}: Cannot extract user info from "{data}"',LOG_ERROR)
            self.sendMessage(telegramid, 'Ошибка обработки сообщения. Попробуйте еще раз.')
            return
        # Remove keyboard if set
        self.removeActionKeyboard(actionInfo['buttons'])
        Connection.clearActionButtons(username=username,actionId=actionInfo['id'])
        log(f'{fName}: Removed menu for action {actionInfo["id"]} for {username}')

    def getTimeDateTxt(self, reminder):
        return reminder.strftime("%d-%m-%Y %H:%M:%S")
