from threading import Thread
from db_lib import *
from log_lib import *
from reminder import *
from NeoOperationBot import *

#===============
# Main section
#---------------
def main() -> None:
    global loopFlag
    initLog()
    TESTCONNECTION = isTestDB()
    if (not Connection.initConnection(test=TESTCONNECTION)):
        log(str='Exiting', logLevel=LOG_ERROR)
        return 1
    bot = NeoOperationBot()
    # Run thread
    thread = Thread(target=reminderTask, args=[bot.getBot()])
    thread.start()
    # Start bot
    bot.startBot()
    # Finish thread
    loopFlag = False
    thread.join()
    Connection.closeConnection()
    closeLog()

if __name__ == "__main__":
    main()