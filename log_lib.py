
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

class Log:
    logCurrentLevel = LOG_INFO
    logFileName = ''
    logHandle = None
    printToo = False

    def logFileRotation(logFile):
        # Check if log file exist
        if (path.isfile(path=logFile)):
            # Copy existing file and add '.bak' at the end
            shutil.copyfile(src=logFile, dst=logFile + '.bak')

    # Log startup attempt
    def logStart() -> None:
        load_dotenv()
        # Read logStartFile from env
        logFile = getenv(key=ENV_LOGSTARTFILE)
        if (not logFile):
            logFile = DEFAULT_LOGSTARTFILE
        try:
            f = open(file=logFile, mode='a')
            tzinfo=ZoneInfo(key='Europe/Moscow')
            startTime = dt.now(tz=tzinfo).strftime("%d-%m-%Y %H:%M:%S")
            f.write(f'{startTime}: NeoOperation_bot started'+"\n")
        except Exception as error:
            log(str=f'Cannot open "{logFile}": {error}', logLevel=LOG_ERROR)
        f.close()

def initLog(logFile=None, printToo=False) -> None:
    load_dotenv()
    if (not logFile):
        # Read logFile from env
        logFile = getenv(key=ENV_LOGFILE)
        if (not logFile):
            logFile = DEFAULT_LOGFILE
    Log.logFileName = logFile
    # Read log level from ENV
    logLevel = getenv(key=ENV_LOGLEVEL)
    if (logLevel):
        # Check that this level exist
        ret = LOG_LEVELS.get(logLevel)
        if (ret): # ENV log level exists
            Log.logCurrentLevel = logLevel
    # Check if need to printout messages
    printTooEnv = getenv(key=ENV_PRINTTOO)
    if (printTooEnv and printTooEnv == 'True'):
        printToo = True
    Log.logFileRotation(logFile=logFile)
    # Open log file for writing
    try:
        f = open(file=logFile, mode='w')
        Log.logHandle = f
    except Exception as error:
        log(str=f'Cannot open "{logFile}": {error}', logLevel=LOG_ERROR)
    if (printToo == True):
        Log.printToo = printToo
    Log.logStart()
    log(str=f'Log initialization complete: log file={Log.logFileName} | log level={Log.logCurrentLevel}')

def log(str, logLevel=LOG_INFO):
    # Check log level first
    if (LOG_LEVELS[logLevel] > LOG_LEVELS[Log.logCurrentLevel]):
        return # Do not print
    if (not Log.logHandle):
        print(str)
    else:
        # Get date and time
        tzinfo=ZoneInfo('Europe/Moscow')
        time: str = dt.now(tz=tzinfo).strftime("%d-%m-%Y %H:%M:%S")
        logStr: str = f'[{time}]:{logLevel}:{str}'
        Log.logHandle.write(logStr+"\n")
        Log.logHandle.flush()
        # Print message if set
        if (Log.printToo == True):
            print(logStr)

def closeLog() -> None:
    if (Log.logHandle):
        log(str=f'Closing log')
        Log.logHandle.close()
