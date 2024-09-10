
from os import path
from os import getenv
from dotenv import load_dotenv
import shutil
from datetime import datetime as dt
from zoneinfo import ZoneInfo

ENV_LOGFILE = 'LOGFILE'
ENV_LOGSTARTFILE = 'LOGSTARTFILE'
ENV_LOGLEVEL = 'LOGLEVEL'
ENV_PRINTTOO = 'PRINTTOO'

DEFAULT_LOGFILE = '/tmp/neo-operation.log'
DEFAULT_LOGSTARTFILE = '/tmp/neo-operation-starts.log'

LOG_ERROR = 'ERROR'
LOG_INFO = 'INFO'
LOG_WARNING = 'WARNING'
LOG_DEBUG = 'DEBUG'

LOG_LEVELS = {
    LOG_ERROR: 3,
    LOG_WARNING: 4,
    LOG_INFO: 5,
    LOG_DEBUG: 7
}

class GuessImageLog:
    logCurrentLevel = LOG_INFO
    logFileName = ''
    logHandle = None
    printToo = False

    def logFileRotation(logFile):
        # Check if log file exist
        if (path.isfile(logFile)):
            # Copy existing file and add '.bak' at the end
            shutil.copyfile(logFile, logFile + '.bak')

    # Log startup attempt
    def logStart():
        load_dotenv()
        # Read logStartFile from env
        logFile = getenv(ENV_LOGSTARTFILE)
        if (not logFile):
            logFile = DEFAULT_LOGSTARTFILE
        try:
            f = open(logFile, 'a')
            tzinfo=ZoneInfo('Europe/Moscow')
            startTime = dt.now(tzinfo).strftime("%d-%m-%Y %H:%M:%S")
            f.write(f'{startTime}: GuessImage_bot started'+"\n")
        except Exception as error:
            log(f'Cannot open "{logFile}": {error}', LOG_ERROR)
        f.close()

def initLog(logFile=None, printToo=False):
    load_dotenv()
    if (not logFile):
        # Read logFile from env
        logFile = getenv(ENV_LOGFILE)
        if (not logFile):
            logFile = DEFAULT_LOGFILE
    GuessImageLog.logFileName = logFile
    # Read log level from ENV
    logLevel = getenv(ENV_LOGLEVEL)
    if (logLevel):
        # Check that this level exist
        ret = LOG_LEVELS.get(logLevel)
        if (ret): # ENV log level exists
            GuessImageLog.logCurrentLevel = logLevel
    # Check if need to printout messages
    printTooEnv = getenv(ENV_PRINTTOO)
    if (printTooEnv and printTooEnv == 'True'):
        printToo = True
    GuessImageLog.logFileRotation(logFile)
    # Open log file for writing
    try:
        f = open(logFile, 'w')
        GuessImageLog.logHandle = f
    except Exception as error:
        log(f'Cannot open "{logFile}": {error}', LOG_ERROR)
    if (printToo == True):
        GuessImageLog.printToo = printToo
    GuessImageLog.logStart()
    log(f'Log initialization complete: log file={GuessImageLog.logFileName} | log level={GuessImageLog.logCurrentLevel}')

def log(str, logLevel=LOG_INFO):
    # Check log level first
    if (LOG_LEVELS[logLevel] > LOG_LEVELS[GuessImageLog.logCurrentLevel]):
        return # Do not print
    if (not GuessImageLog.logHandle):
        print(str)
    else:
        # Get date and time
        tzinfo=ZoneInfo('Europe/Moscow')
        time = dt.now(tzinfo).strftime("%d-%m-%Y %H:%M:%S")
        logStr = f'[{time}]:{logLevel}:{str}'
        GuessImageLog.logHandle.write(logStr+"\n")
        GuessImageLog.logHandle.flush()
        # Print message if set
        if (GuessImageLog.printToo == True):
            print(logStr)

def closeLog():
    if (GuessImageLog.logHandle):
        log(f'Closing log')
        GuessImageLog.logHandle.close()
