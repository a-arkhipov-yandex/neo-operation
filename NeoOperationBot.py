from os import getenv
from dotenv import load_dotenv
import telebot
from log_lib import *

ENV_BOTTOKEN = 'BOTTOKEN'
ENV_BOTTOKENTEST = 'BOTTOKENTEST'

ENV_TESTDB = 'TESTDB'
ENV_TESTBOT = 'TESTBOT'

VERSION = '0.1'

CMD_HELP = '/help'
CMD_NEWACTION = '/newaction'

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

#=====================
# Bot class
#---------------------
class NeoOperationBot:
    __bot = None

    def initBot():
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

    def isInitialized():
        return (NeoOperationBot.__bot != None)

    # Init bot
    def __init__(self):
        # Check if bot is initialized
        if (not NeoOperationBot.isInitialized()):
            NeoOperationBot.initBot()
        self.bot = NeoOperationBot.__bot

    def startBot(self):
        if (not NeoOperationBot.isInitialized()):
            log(f'Bot is not initialized - cannot start', LOG_ERROR)
            return
        try:
            log(f'Starting bot...')
            self.bot.infinity_polling()
        except KeyboardInterrupt:
            log('Exiting by user request')

    # Message handler
    def get_messages(self, messages):
        if (not NeoOperationBot.isInitialized()):
            log(f'Bot is not initialized - cannot start', LOG_ERROR)
            return
        for message in messages:
            # Check if there is cmd
            if (message.text[0] == '/'):
                return self.cmdHandler(message)
            NeoOperationBot.__bot.send_message(message.from_user.id, 'Я вас не понимаю:(.')
            NeoOperationBot.__bot.send_message(message.from_user.id, self.getHelpMessage(message.from_user.username))

    def cmdHandler(self, message):
        bot = NeoOperationBot.__bot
        text = message.text.lower()
        if text == CMD_HELP:
            bot.send_message(message.from_user.id, self.getHelpMessage(message.from_user.username))
        else:
            bot.send_message(message.from_user.id, "Неизвестная команда.")
            bot.send_message(message.from_user.id, self.getHelpMessage(message.from_user.username))

    # Returns help message
    def getHelpMessage(self, userName):
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
