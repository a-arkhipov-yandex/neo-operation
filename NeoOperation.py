from db_lib import *
from log_lib import *

from NeoOperationBot import *

#===============
# Main section
#---------------
def main():
    initLog()
    TESTCONNECTION = isTestDB()
    Connection.initConnection(test=TESTCONNECTION)
    bot = NeoOperationBot()
    bot.startBot()
    Connection.closeConnection()
    closeLog()

if __name__ == "__main__":
    main()