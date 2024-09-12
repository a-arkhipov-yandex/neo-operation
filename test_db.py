from __future__ import annotations

import pytest

from db_lib import *

class TestDB:
    testUserName1 = "TestUserName1"
    testUserName2 = "TestUserName2"
    testUserId1 = None
    testUserId2 = None

    def testDBConnectoin(self): # Test both test and production connection
        initLog(printToo=True)
        Connection.initConnection(test=False)
        isInit1 = Connection.isInitialized()
        Connection.closeConnection()
        Connection.initConnection(test=True)
        isInit2 = Connection.isInitialized()
        # Create test user
        TestDB.testUserId1 = Connection.addUser(TestDB.testUserName1, 1) # fake telegramid
        TestDB.testUserId2 = Connection.addUser(TestDB.testUserName2, 10) # fake telegramid
        assert(isInit1 and isInit2)
        assert(TestDB.testUserId1 and TestDB.testUserId2)

    @pytest.mark.parametrize(
        "query, params, expected_result",
        [
            # Correct
            ('select id from users where id = 1000000', {}, NOT_FOUND), # Correct query wihtout params returning nothing
            ('select id from users where id = %(c)s', {'c':1000000}, NOT_FOUND), # Correct query with 1 param returning nothing
            ('select id from users where id=%(c)s and name=%(n)s', {'c':1000000, 'n':'test'}, NOT_FOUND), # Correct query with >1 params returning nothing
            # Incorrect
            ('select id from users where people = 10', {}, None), # InCorrect query syntax
            ('select id from users where id = %(c)s', {}, None), # InCorrect query need params but not provided
            ('select id from users where id=%(c)s and name=%(n)s', {'c':1000000}, None), # InCorrect number of params in query
        ],
    )
    def testExecuteQueryFetchOne(self, query, params, expected_result):
        assert(Connection.executeQuery(query, params) == expected_result)

    @pytest.mark.parametrize(
        "query, params, expected_result",
        [
            # Correct
            ('select id from users where id = 1000000', {}, NOT_FOUND), # Correct query wihtout params returning nothing
            ('select id from users where id = %(c)s', {'c':1000000}, NOT_FOUND), # Correct query with 1 param returning nothing
            ('select id from users where id=%(c)s and name=%(n)s', {'c':1000000, 'n':'test'}, NOT_FOUND), # Correct query with >1 params returning nothing
            # Incorrect
            ('select id from users where people = 10', {}, None), # InCorrect query syntax
            ('select id from users where id = %(c)s', {}, None), # InCorrect query need params but not provided
            ('select id from users where id=%(c)s and name=%(n)s', {'c':1000000}, None), # InCorrect number of params in query
        ],
    )
    def testExecuteQueryFetchAll(self, query, params, expected_result):
        assert(Connection.executeQuery(query, params, True) == expected_result)

    # Test user name format
    @pytest.mark.parametrize(
        "p, expected_result",
        [
            ('123dfdf', False),
            ('dfввв12', False),
            ('s232', True),
            ('s232f', True),
            ('s23#2', False),
            ('s/232', False),
            ('s#232', False),
            ('s$232', False),
            ('s%232', False),
            ('s2.32', False),
            ('alex-arkhipov', True),
            ('alex_arkhipov', True),
        ],
    )
    def testCheckUserNameFormat(self, p, expected_result):
        ret = dbLibCheckUserName(p)
        assert(ret == expected_result)

    # TODO: check check statuses and check log types

    # Test getActionStatuses
    def testGetActionStatuses(self):
        ret = Connection.getActionStatuses()
        incorrectStatus1 = dbLibCheckActionStatus(100)
        incorrectStatus2 = dbLibCheckActionStatus('dfsfd')
        incorrectStatus3 = dbLibCheckActionStatus(0)
        incorrectStatus4 = dbLibCheckActionStatus(-4)
        correctStatus1 = dbLibCheckActionStatus(ACTION_COMPLETED)
        assert(len(ret) != 0)
        assert(not incorrectStatus1)
        assert(not incorrectStatus2)
        assert(not incorrectStatus3)
        assert(not incorrectStatus4)
        assert(correctStatus1)

    # Test getUserStates
    def testGetUserStates(self):
        ret = Connection.getUserStates()
        incorrectState1 = dbLibCheckUserState(100)
        incorrectState2 = dbLibCheckUserState('dfdf')
        incorrectState3 = dbLibCheckUserState(0)
        correctState1 = dbLibCheckUserState(STATE_ACTIONTEXT)
        assert(len(ret) != 0)
        assert(not incorrectState1)
        assert(not incorrectState2)
        assert(not incorrectState3)
        assert(correctState1)

    # Test getLogTypes
    def testGetLogTypes(self):
        ret = Connection.getLogTypes()
        incorrectLogType1 = dbLibCheckLogType(100)
        incorrectLogType2 = dbLibCheckLogType(0)
        incorrectLogType3 = dbLibCheckLogType(False)
        incorrectLogType4 = dbLibCheckLogType('dfdsf')
        incorrectLogType5 = dbLibCheckLogType(-100)
        correctLotType1 = dbLibCheckLogType(LOGTYPE_REMINDERSET)
        assert(len(ret) != 0)
        assert(not incorrectLogType1)
        assert(not incorrectLogType2)
        assert(not incorrectLogType3)
        assert(not incorrectLogType4)
        assert(not incorrectLogType5)
        assert(correctLotType1)

    def testUser(self):
        testIncorrectUserName1 = ''; # empty
        testIncorrectUserName2 = 'a'; # too short
        testIncorrectUserName3 = 'adfdf###'; # wrong symbols
        res1 = Connection.addUser(testIncorrectUserName1,1)
        resUserInfo1 = Connection.getUserInfoByName(TestDB.testUserName1)
        resUserState = Connection.getUserState(TestDB.testUserName1)
        resIncorrectUserState = Connection.setUserState('nonexisting_user', STATE_ACTIONTEXT)
        resIncorrectState = Connection.setUserState(TestDB.testUserName1, 25)
        resCorrectState = Connection.setUserState(TestDB.testUserName1, STATE_ACTIONTEXT)
        resUserState2 = Connection.getUserState(TestDB.testUserName1)
        resClearUserState = Connection.clearUserState(TestDB.testUserName1)
        resUserState3 = Connection.getUserState(TestDB.testUserName1)
        res11 = Connection.getUserIdByName(testIncorrectUserName1)
        res2 = Connection.addUser(testIncorrectUserName2,1)
        res3 = Connection.addUser(testIncorrectUserName3,1)
        res4 = Connection.getUserIdByName('nonexisting_user')
        assert(not res1)
        assert(resUserInfo1 and len(resUserInfo1) == 4)
        assert(resUserState == None)
        assert(not resIncorrectUserState)
        assert(not resIncorrectState)
        assert(resCorrectState)
        assert(resUserState2 == STATE_ACTIONTEXT)
        assert(resClearUserState)
        assert(resUserState3 == None)
        assert(res11 == NOT_FOUND)
        assert(not res2)
        assert(not res3)
        assert(res4 == NOT_FOUND)

    # Test actions
    def testActions(self):
        # Create action 1
        actionId1 = Connection.addAction(TestDB.testUserName1,'Test acton 1','Test test 1','')
        # TODO: Check created log added
        logsCreated = Connection.getLogs(actionId=actionId1,logType=LOGTYPE_CREATED)
        resLogCreated = (len(logsCreated) > 0)
        # Create action 2
        actionId2 = Connection.addAction(TestDB.testUserName2,'Test acton 2','Test test 2','')
        # Get list of active actions (must be 1)
        resListActions1 = Connection.getActions(username=TestDB.testUserName1, active=True)
        # Get list of all actions (must be 1)
        resListActions2 = Connection.getActions(username=TestDB.testUserName2, active=False)
        # Get list of all actions of all users (must be 2)
        resListActionsAllUsers1 = Connection.getActions(active=False)
        # Complete action 1
        resCompleteActionWrongUser = Connection.completeAction(username=TestDB.testUserName2, actionId=actionId1)
        resComplete = Connection.completeAction(username=TestDB.testUserName1, actionId=actionId1)
        logsComplete = Connection.getLogs(actionId=actionId1,logType=LOGTYPE_COMPLETED)
        resLogComplete = (len(logsComplete) > 0)
        resCompleteNotexisting = Connection.completeAction(username=TestDB.testUserName1, actionId=1000000)
        # Get list of active actions (must be 0)
        resListActions3 = Connection.getActions(username=TestDB.testUserName1, active=True)
        # Get list of all actions (must be 1)
        resListActions4 = Connection.getActions(username=TestDB.testUserName1, active=False)
        # Cancel action 2
        resCancelActionWrongUser = Connection.completeAction(username=TestDB.testUserName1, actionId=actionId2)
        resCancel = Connection.cancelAction(username=TestDB.testUserName2, actionId=actionId2)
        logsCancelled = Connection.getLogs(actionId=actionId1,logType=LOGTYPE_CREATED)
        resLogCancelled = (len(logsCancelled) > 0)
        resCancelNonexisting = Connection.cancelAction(username=TestDB.testUserName1, actionId=100000000)
        # Get list of active actions (must be 0)
        resListActions5 = Connection.getActions(username=TestDB.testUserName2, active=True)
        # Get list of all actions (must be 1)
        resListActions6 = Connection.getActions(username=TestDB.testUserName2, active=False)
        resListActionsAllUsers2 = Connection.getActions(active=False)
        # Delete all logs and actions
        resDeleteLogs1 = Connection.deleteActionLogs(actionId1)
        resDeleteLogs2 = Connection.deleteActionLogs(actionId2)
        resDelete1 = Connection.deleteAction(actionId1)
        resDelete2 = Connection.deleteAction(actionId2)

        assert(actionId1 != None)
        assert(actionId2 != None)
        assert(len(resListActions1) == 1)
        assert(len(resListActions2) == 1)
        assert(len(resListActions3) == 0)
        assert(len(resListActions4) == 1)
        assert(len(resListActions5) == 0)
        assert(len(resListActions6) == 1)
        assert(len(resListActionsAllUsers1) >= 2)
        assert(len(resListActionsAllUsers2) >= 2)
        assert(resComplete)
        assert(not resCompleteActionWrongUser)
        assert(not resCancelActionWrongUser)
        assert(not resCompleteNotexisting)
        assert(not resCancelNonexisting)
        assert(resCancel)
        assert(resLogCreated)
        assert(resLogComplete)
        assert(resLogCancelled)
        assert(resDeleteLogs1)
        assert(resDeleteLogs2)
        assert(resDelete1)
        assert(resDelete2)

    def testClenup(seft):
        # Remove test user
        resDelete1 = False
        resDelete2 = False
        resDelete1 = Connection.deleteUser(TestDB.testUserId1)
        resDelete2 = Connection.deleteUser(TestDB.testUserId2)
        # Close connection
        Connection.closeConnection()
        assert(resDelete1)
        assert(resDelete2)

