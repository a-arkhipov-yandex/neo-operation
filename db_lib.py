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

STATE_ACTIONTEXT = 1

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

# Check action status
# Returns: True/False
def dbLibCheckActionStatus(status):
    try:
        intStatus = int(status)
    except:
        return False
    statuses = Connection.getActionStatuses()
    return (intStatus >= 1 and intStatus <=len(statuses))

# Check user state
# Returns: True/False
def dbLibCheckUserState(state):
    try:
        intState = int(state)
    except:
        return False
    states = Connection.getUserStates()
    return (intState >= 1 and intState <=len(states))

# Check logType
# Returns: True/False
def dbLibCheckLogType(logType):
    try:
        intLogType = int(logType)
    except:
        return False
    logTypes = Connection.getLogTypes()
    return (intLogType >= 1 and intLogType <=len(logTypes))


#==================
# Class definition
class Connection:
    __connection = None
    __isInitialized = False
    __actionStatuses = {}
    __userStates = {}
    __logTypes = {}

    # Init connection - returns True/False
    def initConnection(token=None, test=False):
        ret = False
        if (not Connection.__isInitialized):
            Connection.__connection = Connection.__newConnection(token, test)
            if (Connection.isInitialized()):
                # Cache section
                Connection.cacheActionStatuses()
                Connection.cacheUserStates()
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

    # Get states from cache
    def getUserStates():
        return Connection.__userStates

    # Read acton statuses and cache them in memory
    def cacheUserStates():
        fName = Connection.cacheUserStates.__name__
        query = 'select id, state from states'
        states = Connection.executeQuery(query=query, params={}, all=True)
        if (dbFound(states)):
            # Cache them in memory
            for state in states:
                id = int(state[0])
                state = state[1]
                Connection.__userStates[id] = state
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
        if (dbFound(rawAction) and (len(rawAction) == 11)):
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
            action['telegramid'] = rawAction[10]
        else:
            action = None
        return action

    # Insert new action in DB
    # Returns:
    #   None - error (db or other)
    #   ID - id of new actoins
    def addAction(username, title, text, fromTxt):
        fName = Connection.addAction.__name__
        if (not Connection.isInitialized()):
            log("{fName}: Cannot insert action - connection is not initialized",LOG_ERROR)
            return None
        ret = dbLibCheckUserName(username)
        if (not ret):
            log(f"{fName}: Cannot insert action -  invalid user name format",LOG_ERROR)
            return None
        ret = None
        # get user id
        userId = Connection.getUserIdByName(username)
        conn = Connection.getConnection()
        if (dbFound(userId)):
            query = '''
                INSERT INTO actions (userid,title,text,"from",created,status)
                VALUES (%(uId)s,%(ti)s,%(te)s,%(fr)s,NOW(),%(st)s)
                RETURNING id
            '''
            params = {'uId':userId,'ti':title,'te':text,'fr':fromTxt,'st':ACTION_ACTIVE}
            with conn.cursor() as cur:
                try:
                    cur.execute(query, params)
                    row = cur.fetchone()
                    if (row):
                        ret = row[0]
                        log(f'{fName}: Inserted action: {username} - {title}')
                    else:
                        log(f'{fName}: Cannot get id of new action: {query}',LOG_ERROR)
                except (Exception, psycopg2.DatabaseError) as error:
                    log(f'{fName}: Failed insert action {username} - {title}: {error}',LOG_ERROR)
            if (ret):
                # Add log
                Connection.addLog(actionId=ret, logType=LOGTYPE_CREATED, noCheck=True) # do not check action existance
        else:
            log(f'{fName}: Cannot get user from DB: {username}',LOG_ERROR)
        return ret

    # Get action info
    def getActionInfo(username, actionId):
        actionInfo = Connection.getActions(username=username, actionId=actionId)
        if (dbFound(actionInfo)):
            actionInfo = actionInfo[0] # Extract the only item
        else:
            actionInfo = NOT_FOUND
        return actionInfo

    # Get all or active (by default) actions for user username
    # Returns:
    #   None - error or no user
    #   [{action1}, ...] - array of user actions
    def getActions(username=None, active=False, actionId=None, withReminders=False):
        fName = Connection.getActions.__name__
        params = {}
        addQuery = ''
        whereQuery = f' where l.logtype = {LOGTYPE_CREATED} '
        if (username):
            addQuery = ' and u.name = %(un)s '
            params['un'] = username
        if (active):
            addQuery = addQuery + ' and a.status = %(st)s '
            params['st'] = ACTION_ACTIVE
        if (actionId):
            addQuery = addQuery + ' and a.id = %(aId)s'
            params['aId'] = actionId
        # Handle reminders
        reminderQuery = ''
        if (withReminders):
            reminderQuery = ' and a.reminder < NOW() '
        query = f'''
            select a.id, a.userid, u.name, a.title, a.text,
                a.from, a.created, a.reminder, a.status, a.completedate, u.telegramid
            from actions as a
            join users as u on u.id = a.userid
            join logs as l on l.actionid = a.id
            {whereQuery} {addQuery} {reminderQuery}
            order by l.time_stamp
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

    def getActionsWithExpiredReminders(username=None):
        return Connection.getActions(username=username, active=True, withReminders=True)

    # Complete action for user username
    # Returns:
    #   False - error or no user or no action
    #   True - action completed successfully
    def completeAction(actionId, username):
        fName = Connection.completeAction.__name__
        # Check that action belongs to user
        actionsInfo = Connection.getActions(actionId=actionId)
        ret = False
        if (dbFound(actionsInfo) and (len(actionsInfo) == 1)):
            actionInfo = actionsInfo[0] # Get the only record
            # Check user
            if (actionInfo['username'] != username):
                log(f'{fName}: Action {actionId} doesnt belog to user {username}', LOG_ERROR)
                return ret
            ret = Connection.completeOrCancelAction(actionId, ACTION_COMPLETED)
            if (ret):
                log(f'Action {actionId} completed')
                Connection.addLog(actionId=actionId, logType=LOGTYPE_COMPLETED)
        else:
            log(f'{fName}: Cannot find action to complete {username} - {actionId}', LOG_ERROR)
        return ret

    # Cancel action for user username
    # Returns:
    #   False - error or no user or no action
    #   True - action completed successfully
    def cancelAction(actionId, username):
        fName = Connection.cancelAction.__name__
        # Check that action belongs to user
        actionsInfo = Connection.getActions(actionId=actionId)
        ret = False
        if (dbFound(actionsInfo) and (len(actionsInfo) == 1)):
            actionInfo = actionsInfo[0] # Get the only record
            # Check user
            if (actionInfo['username'] != username):
                log(f'{fName}: Action {actionId} doesnt belog to user {username}', LOG_ERROR)
                return ret
            ret = Connection.completeOrCancelAction(actionId, ACTION_CANCELLED)
            if (ret):
                log(f'Action {actionId} cancelled')
                Connection.addLog(actionId=actionId, logType=LOGTYPE_CANCELLED)
        else:
            log(f'{fName}: Cannot find action to cancel {username} - {actionId}', LOG_ERROR)
        return ret

    # Complete or Cancel action for user username
    # Returns:
    #   False - error or no user or no action
    #   True - action completed successfully
    def completeOrCancelAction(actionId, status):
        fName = Connection.completeOrCancelAction.__name__
        # Check new status first
        if (status != ACTION_COMPLETED and status != ACTION_CANCELLED):
            log(f"{fName}: Wrong status provided {actionId} - {status}",LOG_ERROR)
            return False
        if (not Connection.isInitialized()):
            log(f"{fName}: Cannot complete or cancel action {actionId} - connection is not initialized",LOG_ERROR)
            return False
        ret = False
        actionsInfo = Connection.getActions(actionId=actionId)
        if (actionsInfo == None):
            log(f'{fName}: cannot get action {actionId}: DB issue',LOG_ERROR)
            return ret
        if (dbFound(actionsInfo)):
            actionInfo = actionsInfo[0] # get first and the only element
            # Check that action is not completed yet
            if (actionInfo['status'] != ACTION_ACTIVE):
                log(f'{fName}: Action {actionId} is already completed - cannot complete', LOG_ERROR)
                return False

            conn = Connection.getConnection()
            with conn.cursor() as cur:
                query = 'update actions set completedate = NOW(), status=%(st)s , reminder=%(rem)s where id = %(id)s'
                try:
                    cur.execute(query,{'st':status,'id':actionId, 'rem':None})
                    log(f'{fName}: Updated action: {actionId} - {status}')
                    ret = True
                except (Exception, psycopg2.DatabaseError) as error:
                    log(f'{fName}: Failed complete or cancel action {actionId}: {error}',LOG_ERROR)
        else:
            log(f"{fName}: Cannot find action {actionId}",LOG_ERROR)
        return ret

    # Delete action - returns True/False
    def deleteAction(actionId):
        fName = Connection.deleteAction.__name__
        ret = False
        if (not Connection.isInitialized()):
            log(f"{fName}: Cannot delete action {actionId} - connection is not initialized",LOG_ERROR)
            return ret
        # Check that action exist
        actionsInfo = Connection.getActions(actionId=actionId)
        if (dbFound(actionsInfo)):
            # Delete action logs first
            Connection.deleteActionLogs(actionId=actionId)
            conn = Connection.getConnection()
            with conn.cursor() as cur:
                query = "DELETE from actions where id = %(a)s"
                try:
                    cur.execute(query, {'a':actionId})
                    log(f'Deleted action: {actionId}')
                    ret = True
                except (Exception, psycopg2.DatabaseError) as error:
                    log(f'{fName}: Failed delete action {actionId}: {error}',LOG_ERROR)
        else:
            log(f'{fName}: Cannot find action to delete {actionId}')
        return ret

    #===============
    # User section
    #---------------
    def parseUserData(rawUser):
        userInfo = {}
        if (dbFound(rawUser) and (len(rawUser) == 4)):
            userInfo['id'] = int(rawUser[0])
            userInfo['name'] = rawUser[1]
            userInfo['telegramid'] = rawUser[2]
            try:
                userInfo['state'] = int(rawUser[3])
            except:
                userInfo['state'] = None
        else:
            userInfo = None
        return userInfo

    # Insert new user in DB
    # Returns:
    #   None - if error of duplicate username
    #   id - new user id
    def addUser(username, telegramid):
        fName = Connection.addUser.__name__
        if (not Connection.isInitialized()):
            log("{fName}: Cannot insert user - connection is not initialized",LOG_ERROR)
            return None
        ret = dbLibCheckUserName(username)
        if (not ret):
            log(f"{fName}: Cannot insert user -  invalid name format",LOG_ERROR)
            return None
        ret = None
        conn = Connection.getConnection()
        # Check for duplicates
        retUser = Connection.getUserIdByName(username)
        if (retUser == None): # error with DB
            log(f'{fName}: Cannot get user from DB: {username}',LOG_ERROR)
            return ret
        if (dbNotFound(retUser)):
            with conn.cursor() as cur:
                query = "INSERT INTO users (name, telegramid) VALUES (%(u)s, %(tId)s) RETURNING id"
                try:
                    cur.execute(query, {'u':username, 'tId': telegramid})
                    row = cur.fetchone()
                    if (row):
                        ret = row[0]
                        log(f'Inserted user: {username}')
                except (Exception, psycopg2.DatabaseError) as error:
                    log(f'{fName}: Failed insert user {username}: {error}',LOG_ERROR)
        else:
            log(f'{fName}: Trying to insert duplicate user: {username}',LOG_WARNING)
            ret = retUser # Return true for now - probably wrong
        return ret

    # Get user by name
    # Return:
    #   None - something wrong with connection/query
    #   id - user id
    #   NOT_FOUND - no such user
    def getUserIdByName(username):
        ret = dbLibCheckUserName(username)
        if (not ret):
            return NOT_FOUND
        query = f"SELECT id FROM users WHERE name = %(name)s"
        ret = Connection.executeQuery(query,{'name':username})
        if (dbFound(ret)):
            ret = ret[0]
        return ret

    # Get userInfo by name
    # Return:
    #   None - something wrong with connection/query
    #   {userInfo} - user info
    #   NOT_FOUND - no such user
    def getUserInfoByName(username):
        ret = dbLibCheckUserName(username)
        if (not ret):
            return NOT_FOUND
        query = f"SELECT id, name, telegramid, state FROM users WHERE name = %(name)s"
        ret = Connection.executeQuery(query,{'name':username})
        if (dbFound(ret)):
            ret = Connection.parseUserData(ret)
        return ret
    
    # Get user state
    def getUserState(username):
        ret = Connection.getUserInfoByName(username=username)
        if (dbFound(ret)):
            ret = ret['state']
        return ret
    
    # Set user state
    # Return: True/False
    def setUserState(username, state):
        fName = Connection.setUserState.__name__
        ret = dbLibCheckUserName(username)
        if (not ret):
            return False
        # Check that user exists
        userInfo = Connection.getUserInfoByName(username=username)
        if (not dbFound(userInfo)):
            log(f'{fName}: No such user {username}', LOG_ERROR)
            return False
        # Check state
        if ((state != None) and (not dbLibCheckUserState(state))):
            log(f'{fName}: Unknown state {state} for user {username}', LOG_ERROR)
            return False
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = 'update users set state = %(st)s where id = %(id)s'
            try:
                cur.execute(query,{'st':state,'id':userInfo['id']})
                log(f'{fName}: Updated user state: {username} - {state}')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                log(f'{fName}: Failed set state {username}: {error}',LOG_ERROR)
        return ret

    # Clear user state
    # Return: True/False
    def clearUserState(username):
        return Connection.setUserState(username=username, state=None)

    # Delete user - returns True/False
    def deleteUser(userId):
        fName = Connection.deleteUser.__name__
        ret = False
        if (not Connection.isInitialized()):
            log(f"{fName}: Cannot delete user {userId} - connection is not initialized",LOG_ERROR)
            return ret
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = "DELETE from users where id = %(user)s"
            try:
                cur.execute(query, {'user':userId})
                log(f'Deleted user: {userId}')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                log(f'{fName}: Failed delete user {userId}: {error}',LOG_ERROR)
        return ret

    #============
    # Log section
    #------------
    def parseLogData(rawLog):
        log = {}
        if (dbFound(rawLog) and (len(rawLog) == 5)):
            log['id'] = int(rawLog[0])
            log['actionid'] = int(rawLog[1])
            log['logtype'] = rawLog[2]
            log['comment'] = rawLog[3]
            log['time_stamp'] = rawLog[4]
        else:
            log = None
        return log

    # Add log recored
    # Returns: True/False
    def addLog(actionId, logType, comment='', noCheck=False):
        fName = Connection.addLog.__name__
        # Check log type first
        if (not dbLibCheckLogType(logType)):
            log(f'{fName}: Incorrect log type provided {logType}', LOG_ERROR)
            return False
        if (not noCheck):
            # Check if action exists
            actionInfo = Connection.getActions(actionId=actionId)
            if (dbFound(actionInfo)): # action exist
                pass
            else:
                log(f'{fName}: Cannot find action ID to add log {actionId}', LOG_ERROR)
                return False
        query = '''
            insert into logs (actionid,logtype,comment,time_stamp) values (%(aId)s,%(lt)s,%(c)s,NOW())
        '''
        params = {'aId':actionId,'lt':logType,'c':comment}
        ret = False
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            try:
                cur.execute(query, params)
                log(f'Inserted log: {actionId} - {logType}')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                log(f'{fName}: Failed insert log {actionId} - {logType}: {error}',LOG_ERROR)
        return ret

    # Delete all logs for action - returns True/False
    def deleteActionLogs(actionId, username=None):
        fName = Connection.deleteActionLogs.__name__
        ret = False
        if (not Connection.isInitialized()):
            log(f"{fName}: Cannot delete action logs {actionId} - connection is not initialized",LOG_ERROR)
            return ret
        actionInfo = Connection.getActions(username=username, actionId=actionId)
        if (dbFound(actionInfo)): # action exist
            conn = Connection.getConnection()
            with conn.cursor() as cur:
                query = "DELETE from logs where actionid = %(aId)s"
                try:
                    cur.execute(query, {'aId':actionId})
                    log(f'Deleted action logs: {actionId}')
                    ret = True
                except (Exception, psycopg2.DatabaseError) as error:
                    log(f'{fName}: Failed delete action logs {actionId}: {error}',LOG_ERROR)
        else:
            log(f'{fName}: Cannot delete action logs {actionId} - no action found', LOG_ERROR)
            ret = False
        return ret
    
    # Get all logs from DB
    # Return:
    #   None - error
    #   [{log1},{},...] - array of logs
    def getLogs(actionId, logType=None):
        fName = Connection.getLogs.__name__
        ret = None
        if (not Connection.isInitialized()):
            log(f"{fName}: Cannot get action logs {actionId} - connection is not initialized",LOG_ERROR)
            return ret
        # Check log type first
        addQuery = ''
        params = {'aId':actionId}
        if (logType):
            if (not dbLibCheckLogType(logType)):
                log(f'{fName}: Incorrect log type provided {logType}', LOG_ERROR)
                return ret
            addQuery = ' and logtype=%(lt)s'
            params['lt'] = logType
        # Check that action exists
        actionsInfo = Connection.getActions(actionId=actionId)
        if (not dbFound(actionsInfo)): # action is there
            log(f'{fName}: No action {actionId}', LOG_ERROR)
            return ret
        query = f'''
            select id,actionid,logtype,comment,time_stamp from logs
            where actionid = %(aId)s {addQuery}
        '''
        logs = []
        retLogs = Connection.executeQuery(query=query, params=params, all=True)
        if (dbFound(retLogs)):
            for rawLog in retLogs:
                log = Connection.parseLogData(rawLog)
                logs.append(log)
        return logs

    #=======================
    # Reminder section
    #-----------------------
    # Set user state
    # Input: timedate object - for set/ None - for cancel
    # Return: True/False
    def setReminder(username, actionId, reminder):
        fName = Connection.setReminder.__name__
        actionInfo = Connection.getActionInfo(username=username, actionId=actionId)
        if (not dbFound(actionInfo)):
            log(f'{fName}: Cannot find action id {username} - {actionId}', LOG_ERROR)
            return False
        # Check that reminder is active
        if ((actionInfo['status'] != ACTION_ACTIVE) and (reminder != None)):
            log(f'{fName}: Cannot set reminder for NOT active action {username} - {actionId} - {reminder}', LOG_ERROR)
            return False
        ret = False
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = 'update actions set reminder = %(r)s where id = %(id)s'
            try:
                cur.execute(query,{'r':reminder,'id':actionId})
                log(f'{fName}: Reminder set for user {username}, action {actionId}, reminder {reminder}')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                log(f'{fName}: Failed set reminder for {username} - {actionId} - {reminder}: {error}',LOG_ERROR)
        if (ret):
            # Add log
            if (reminder == None):
                Connection.addLog(actionId=actionId,logType=LOGTYPE_REMINDERSTOP)
            else:
                Connection.addLog(actionId=actionId,logType=LOGTYPE_REMINDERSET)
        return ret
    
    def clearReminder(username, actionId):
        fName = Connection.clearReminder.__name__
        ret = Connection.setReminder(username=username, actionId=actionId, reminder=None)
        if (ret):
            log(f'{fName}: Reminder cleared for user {username} and action {actionId}')
        else:
            log(f'{fName}: Error clear reminder for user {username} and action {actionId}', LOG_ERROR)
        return ret
    
    # Returns:
    #   None - error
    #   Reminder for acton actionId
    def getReminder(username, actionId):
        fName = Connection.getReminder.__name__
        actionInfo = Connection.getActionInfo(username=username, actionId=actionId)
        if (not dbFound(actionInfo)):
            log(f'{fName}: Cannot find action id {username} - {actionId}', LOG_ERROR)
            return None
        query = 'select reminder from actions where id=%(aId)s'
        params = {'aId':actionId}
        ret = None
        reminder = Connection.executeQuery(query=query, params=params)
        if (dbFound(reminder)):
            ret = reminder[0]
        else:
            log(f'{fName}: Cannot get reminder for user {username}, action {actionId}', LOG_ERROR)
        return ret
