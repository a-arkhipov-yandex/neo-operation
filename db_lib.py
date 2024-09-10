import psycopg2
from log_lib import *

ENV_DBHOST = 'DBHOST'
ENV_DBPORT = 'DBPORT'
ENV_DBNAME = 'DBNAME'
ENV_DBUSER = 'DBUSER'
ENV_DBTOKEN ='DBTOKEN'
ENV_DBTESTHOST = 'DBTESTHOST'
ENV_DBTESTPORT = 'DBTESTPORT'
ENV_DBTESTNAME = 'DBTESTNAME'
ENV_DBTESTUSER = 'DBTESTUSER'
ENV_DBTESTTOKEN ='DBTESTTOKEN'

ENV_BOTTOKEN = 'BOTTOKEN'
ENV_BOTTOKENTEST = 'BOTTOKENTEST'

ENV_TESTDB = 'TESTDB'
ENV_TESTBOT = 'TESTBOT'

NOT_FOUND = "!!!NOT_FOUND!!!"

#=======================
# Common functions section
#-----------------------
# Check that item not found
# Returns:
#   True - item was not found
#   False - otherwise (found or error)
def dbNotFound(result):
    if (result != None):
        if (result == NOT_FOUND): # empty array
            return True
    return False

# Check that item is found
# Returns:
#   True - item has been found
#   False - otherwise (not found or error)
def dbFound(result):
    if (result != None):
        if (result != NOT_FOUND): # empty array
            return True
    return False

def getDBbConnectionData():
    load_dotenv()
    data={}
    data['dbhost']=getenv(ENV_DBHOST)
    data['dbport']=getenv(ENV_DBPORT)
    data['dbname']=getenv(ENV_DBNAME)
    data['dbuser']=getenv(ENV_DBUSER)
    data['dbtoken']=getenv(ENV_DBTOKEN)
    for v in data.values():
        if (v == None): # Something wrong
            return None
    return data

def getDBbTestConnectionData():
    load_dotenv()
    data={}
    data['dbhost']=getenv(ENV_DBTESTHOST)
    data['dbport']=getenv(ENV_DBTESTPORT)
    data['dbname']=getenv(ENV_DBTESTNAME)
    data['dbuser']=getenv(ENV_DBTESTUSER)
    data['dbtoken']=getenv(ENV_DBTESTTOKEN)
    for v in data.values():
        if (v == None): # Something wrong
            return None
    return data

#==================
# Class definition
class Connection:
    __connection = None
    __isInitialized = False

    # Init connection - returns True/False
    def initConnection(token=None, test=False):
        ret = False
        if (not Connection.__isInitialized):
            Connection.__connection = Connection.__newConnection(token, test)
            if (Connection.isInitialized()):
                # Cache section

                log(f"DB Connection created (test={test})", LOG_DEBUG)
                ret = True
            else:
                log(f'Cannot initialize connection to DB',LOG_ERROR)
        else:
                log(f'Trying to initialize connection that already initialized',LOG_WARNING)
        return ret
    
    def getConnection():
        if (not Connection.isInitialized()):
            return None
        return Connection.__connection
    
    def closeConnection():
        if (Connection.__isInitialized):
            Connection.__connection.close()
            Connection.__isInitialized = False
            log(f"DB Connection closed")

    def __newConnection(token=None, test=False):
        conn = None
        try:
            if (test):
                data = getDBbTestConnectionData()
            else: # Production
                data = getDBbConnectionData()
            if (data == None):
                log(f'Cannot get env data. Exiting.',LOG_ERROR)
                return

            conn = psycopg2.connect(f"""
                host={data['dbhost']}
                port={data['dbport']}
                sslmode=verify-full
                dbname={data['dbname']}
                user={data['dbuser']}
                password={data['dbtoken']}
                target_session_attrs=read-write
            """)
            conn.autocommit = True
            Connection.__isInitialized = True
            log(f'DB Connetion established')
        except (Exception, psycopg2.DatabaseError) as error:
            log(f"Cannot connect to database: {error}",LOG_ERROR)
            conn = None
        
        return conn

    def isInitialized():
        return Connection.__isInitialized
