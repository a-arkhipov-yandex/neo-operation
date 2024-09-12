import re
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

ACTION_ACTIVE = 1
ACTION_COMPLETED = 2
ACTION_CANCELLED = 3

LOGTYPE_CREATED = 1
LOGTYPE_CANCELLED = 2
LOGTYPE_COMPLETED = 3
LOGTYPE_UPDATED = 4
LOGTYPE_REMINDERSET = 5
LOGTYPE_REMINDERSTOP = 6

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

# Check user name (can be string with '[a-zA-Z][0-9a-zA-Z]')
def dbLibCheckUserName(userName):
    if (userName == None):
        return False
    ret = False
    res = re.match(r'^[a-zA-Z][a-zA-Z0-9-_]+$', userName)
    if res and len(userName) > 2:
        ret = True
    return ret

#==================
# Class definition
class Connection:
    __connection = None
    __isInitialized = False
    __actionStatuses = {}
    __logTypes = {}

    # Init connection - returns True/False
    def initConnection(token=None, test=False):
        ret = False
        if (not Connection.__isInitialized):
            Connection.__connection = Connection.__newConnection(token, test)
            if (Connection.isInitialized()):
                # Cache section
                Connection.cacheActionStatuses()
                Connection.cacheLogTypes()
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

    # Execute query with params
    # If 'all' == True - execute fetchAll()/ otherwise fetchOne()
    # Returns:
    #   None - issue with execution
    #   NOT_FOUND - if nothing found
    #   [result] - array with one/many found item(s)
    def executeQuery(query, params={}, all=False):
        if (not Connection.isInitialized()):
            log(f'Cannot execute query "{query}" with "{params}" (all={all}): connection is not initialized', LOG_ERROR)
            return None
        ret = NOT_FOUND
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            try:
                cur.execute(query,params)
                if (all):
                    res = cur.fetchall()
                    if (len(res) == 0):
                        ret = NOT_FOUND
                    else:
                        ret = []
                        for i in res:
                            tmp = []
                            for j in i:
                                tmp.append(j)
                            ret.append(tmp)
                else:
                    res = cur.fetchone()
                    if (res):
                        if (len(res) == 0):
                            ret = NOT_FOUND
                        else:
                            ret = []
                            for i in res:
                                ret.append(i)
            except (Exception, psycopg2.DatabaseError) as error:
                log(f'Failed execute query "{query}" with params "{params}" (all={all}): {error}',LOG_ERROR)
                return None
        return ret

    # Get action statuses from cache
    def getActionStatuses():
        return Connection.__actionStatuses

    # Read acton statuses and cache them in memory
    def cacheActionStatuses():
        fName = Connection.cacheActionStatuses.__name__
        query = 'select id, name from statuses'
        statuses = Connection.executeQuery(query=query, params={}, all=True)
        if (dbFound(statuses)):
            # Cache them in memory
            for status in statuses:
                id = int(status[0])
                st = status[1]
                Connection.__actionStatuses[id] = st
        else:
            log(f'{fName}: cannot get statuses from DB: {query}')
            return False
        return True

    # Get action statuses from cache
    def getLogTypes():
        return Connection.__logTypes

    # Read acton statuses and cache them in memory
    def cacheLogTypes():
        fName = Connection.cacheLogTypes.__name__
        query = 'select id, type from logtypes'
        logTypes = Connection.executeQuery(query=query, params={}, all=True)
        if (dbFound(logTypes)):
            # Cache them in memory
            for logType in logTypes:
                id = int(logType[0])
                lType = logType[1]
                Connection.__logTypes[id] = lType
        else:
            log(f'{fName}: cannot get statuses from DB: {query}')
            return False
        return True

    #================
    # Action section
    #----------------
    def parseActionData(rawAction):
        action = {}
        if (dbFound(rawAction) or (len(rawAction) != 10)):
            action['id'] = int(rawAction[0])
            action['userid'] = int(rawAction[1])
            action['username'] = rawAction[2]
            action['title'] = rawAction[3]
            action['text'] = rawAction[4]
            action['from'] = rawAction[5]
            action['created'] = rawAction[6]
            action['reminder'] = rawAction[7]
            action['status'] = rawAction[8]
            action['completedate'] = rawAction[9]
        else:
            action = None
        return action

    # Insert new action in DB
    # Returns:
    #   None - error (db or other)
    #   ID - id of new actoins
    def addAction(userName, title, text, fromTxt):
        fName = Connection.addAction.__name__
        if (not Connection.isInitialized()):
            log("{fName}: Cannot insert action - connection is not initialized",LOG_ERROR)
            return None
        ret = dbLibCheckUserName(userName)
        if (not ret):
            log(f"{fName}: Cannot insert action -  invalid user name format",LOG_ERROR)
            return None
        ret = None
        conn = Connection.getConnection()
        # Check for duplicates
        userId = Connection.getUserIdByName(userName)
        if (dbFound(userId)):
            with conn.cursor() as cur:
                query = '''
                    INSERT INTO actions (userid,title,text,"from",created,status)
                    VALUES (%(uId)s,%(ti)s,%(te)s,%(fr)s,NOW(),%(st)s)
                    RETURNING id
                '''
                params = {'uId':userId,'ti':title,'te':text,'fr':fromTxt,'st':ACTION_ACTIVE}
                try:
                    cur.execute(query, params)
                    row = cur.fetchone()
                    if (row):
                        ret = row[0]
                        log(f'{fName}: Inserted action: {userName} - {title}')
                    else:
                        log(f'{fName}: Cannot get id of new action: {query}',LOG_ERROR)
                except (Exception, psycopg2.DatabaseError) as error:
                    log(f'{fName}: Failed insert action {userName} - {title}: {error}',LOG_ERROR)
        else:
            log(f'{fName}: Cannot get user from DB: {userName}',LOG_ERROR)
        return ret

    # Get all or active (by default) actions for user username
    # Returns:
    #   None - error or no user
    #   [{action1}, ...] - array of user actions
    def getUserActions(username, active=False, actionId=None):
        fName = Connection.getUserActions.__name__
        params = {'un': username}
        addQuery = ''
        if (active):
            addQuery = ' and a.status = %(st)s'
            params['st'] = ACTION_ACTIVE
        elif (actionId):
            addQuery = ' and a.id = %(aId)s'
            params['aId'] = actionId
        query = f'''
            select a.id, a.userid, u.name, a.title, a.text, a.from, a.created, a.reminder, a.status, a.completedate
            from actions as a
            join users as u on u.id = a.userid
            where u.name = %(un)s {addQuery}
        '''
        # Execute query
        actions = []
        actionsRet = Connection.executeQuery(query=query, params=params, all=True)
        if (dbFound(actionsRet)):
            for rawAction in actionsRet:
                action = Connection.parseActionData(rawAction)
                if (action):
                    actions.append(action)
        elif (actionsRet == None):
            log(f'{fName}: cannot get user actions: {query} | {params}: DB issue', LOG_ERROR)
            actions = None
        else:
            # For list return [] for actionId - NOT FOUND
            if (actionId):
                actions = NOT_FOUND
        return actions

    # Complete action for user username
    # Returns:
    #   False - error or no user or no action
    #   True - action completed successfully
    def completeUserAction(username, actionId):
        return Connection.completeOrCancelAction(username, actionId, ACTION_COMPLETED)

    # Cancel action for user username
    # Returns:
    #   False - error or no user or no action
    #   True - action completed successfully
    def cancelUserAction(username, actionId):
        return Connection.completeOrCancelAction(username, actionId, ACTION_CANCELLED)

    # Complete or Cancel action for user username
    # Returns:
    #   False - error or no user or no action
    #   True - action completed successfully
    def completeOrCancelAction(username, actionId, status):
        fName = Connection.completeOrCancelAction.__name__
        # Check new status first
        if (status != ACTION_COMPLETED and status != ACTION_CANCELLED):
            log(f"{fName}: Wrong status provided {username} - {actionId} - {status}",LOG_ERROR)
            return False
        if (not Connection.isInitialized()):
            log(f"{fName}: Cannot complete or cancel action {username} - {actionId} - connection is not initialized",LOG_ERROR)
            return False
        actionsInfo = Connection.getUserActions(username=username, actionId=actionId)
        if (actionsInfo == None):
            log(f'{fName}: cannot get action {actionId}: DB issue',LOG_ERROR)
            return False
        ret = False
        if (dbFound(actionsInfo)):
            actionInfo = actionsInfo[0] # get first and the only element
            # Check that action is not completed yet
            if (actionInfo['status'] != ACTION_ACTIVE):
                log(f'{fName}: Action {actionId} is already completed - cannot complete', LOG_ERROR)
                return False

            conn = Connection.getConnection()
            with conn.cursor() as cur:
                query = 'update actions set completedate = NOW(), status=%(st)s where id = %(id)s'
                try:
                    cur.execute(query,{'st':status,'id':actionId})
                    log(f'{fName}: Updated action: {actionId} - {status}')
                    # TODO: update log table here !!!
                    ret = True
                except (Exception, psycopg2.DatabaseError) as error:
                    log(f'{fName}: Failed complete or cancel action {actionId}: {error}',LOG_ERROR)
        else:
            log(f"{fName}: Cannot find action {actionId}",LOG_ERROR)
        return ret

    # Delete action - returns True/False
    def deleteAction(id):
        fName = Connection.deleteAction.__name__
        ret = False
        if (not Connection.isInitialized()):
            log(f"{fName}: Cannot delete action {id} - connection is not initialized",LOG_ERROR)
            return ret
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = "DELETE from actions where id = %(a)s"
            try:
                cur.execute(query, {'a':id})
                log(f'Deleted action: {id}')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                log(f'{fName}: Failed delete action {id}: {error}',LOG_ERROR)
        return ret

    #===============
    # User section
    #---------------
    # Insert new user in DB. Returns True is success or False otherwise
    def addUser(userName, telegramId):
        fName = Connection.addUser.__name__
        if (not Connection.isInitialized()):
            log("{fName}: Cannot insert user - connection is not initialized",LOG_ERROR)
            return False
        ret = dbLibCheckUserName(userName)
        if (not ret):
            log(f"{fName}: Cannot insert user -  invalid name format",LOG_ERROR)
            return False
        ret = False
        conn = Connection.getConnection()
        # Check for duplicates
        retUser = Connection.getUserIdByName(userName)
        if (retUser == None): # error with DB
            log(f'{fName}: Cannot get user from DB: {userName}',LOG_ERROR)
            return False
        if (dbNotFound(retUser)):
            with conn.cursor() as cur:
                query = "INSERT INTO users (name, telegramid) VALUES (%(u)s, %(tId)s)"
                try:
                    cur.execute(query, {'u':userName, 'tId': telegramId})
                    log(f'Inserted user: {userName}')
                    ret = True
                except (Exception, psycopg2.DatabaseError) as error:
                    log(f'{fName}: Failed insert user {userName}: {error}',LOG_ERROR)
        else:
            log(f'{fName}: Trying to insert duplicate user: {userName}',LOG_WARNING)
            ret = True # Return true for now - probably wrong
        return ret

    # Get user by name
    # Return:
    #   None - something wrong with connection/query
    #   id - user id
    #   NOT_FOUND - no such user
    def getUserIdByName(name):
        ret = dbLibCheckUserName(name)
        if (not ret):
            return NOT_FOUND
        query = f"SELECT id FROM users WHERE name = %(name)s"
        ret = Connection.executeQuery(query,{'name':name})
        if (dbFound(ret)):
            ret = ret[0]
        return ret

    # Delete user - returns True/False
    def deleteUser(id):
        fName = Connection.deleteUser.__name__
        ret = False
        if (not Connection.isInitialized()):
            log(f"{fName}: Cannot delete user {id} - connection is not initialized",LOG_ERROR)
            return ret
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = "DELETE from users where id = %(user)s"
            try:
                cur.execute(query, {'user':id})
                log(f'Deleted user: {id}')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                log(f'{fName}: Failed delete user {id}: {error}',LOG_ERROR)
        return ret
