from __future__ import annotations

import pytest

from db_lib import *

class TestDB:
    testUserName = "TestUserName"

    def testDBConnectoin(self): # Test both test and production connection
        initLog(printToo=True)
        Connection.initConnection(test=False)
        isInit1 = Connection.isInitialized()
        Connection.closeConnection()
        Connection.initConnection(test=True)
        isInit2 = Connection.isInitialized()
        # Create test user
        resAddUser = Connection.addUser(TestDB.testUserName, 1) # fake telegramid
        assert(isInit1 and isInit2)
        assert(resAddUser)

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

    # Test getActionStatuses
    def testGetActionStatuses(self):
        ret = Connection.getActionStatuses()
        assert(len(ret) == 3)

    # Test getLogTypes
    def testGetLogTypes(self):
        ret = Connection.getLogTypes()
        assert(len(ret) == 6)

    def testUser(self):
        testIncorrectUserName1 = ''; # empty
        testIncorrectUserName2 = 'a'; # too short
        testIncorrectUserName3 = 'adfdf###'; # wrong symbols
        res1 = Connection.addUser(testIncorrectUserName1,1)
        res11 = Connection.getUserIdByName(testIncorrectUserName1)
        res2 = Connection.addUser(testIncorrectUserName2,1)
        res3 = Connection.addUser(testIncorrectUserName3,1)
        res4 = Connection.getUserIdByName('nonexisting_user')
        assert(not res1)
        assert(res11 == NOT_FOUND)
        assert(not res2)
        assert(not res3)
        assert(res4 == NOT_FOUND)

    # Test actions
    def testActions(self):
        # Create action 1
        actionId1 = Connection.addAction(TestDB.testUserName,'Test acton 1','Test test 1','')
        # Create action 2
        actionId2 = Connection.addAction(TestDB.testUserName,'Test acton 2','Test test 2','')
        # Get list of active actions (must be 2)
        resListActions1 = Connection.getUserActions(username=TestDB.testUserName, active=True)
        # Get list of all actions (must be 2)
        resListActions2 = Connection.getUserActions(username=TestDB.testUserName, active=False)
        # Complete action 1
        resComplete = Connection.completeUserAction(username=TestDB.testUserName, actionId=actionId1)
        resCompleteNotexisting = Connection.completeUserAction(TestDB.testUserName, 1000000)
        # Get list of active actions (must be 1)
        resListActions3 = Connection.getUserActions(username=TestDB.testUserName, active=True)
        # Get list of all actions (must be 2)
        resListActions4 = Connection.getUserActions(username=TestDB.testUserName, active=False)
        # Cancel action 2
        resCancel = Connection.cancelUserAction(TestDB.testUserName, actionId2)
        resCancelNonexisting = Connection.cancelUserAction(TestDB.testUserName, 100000000)
        # Get list of active actions (must be 0)
        resListActions5 = Connection.getUserActions(username=TestDB.testUserName, active=True)
        # Get list of all actions (must be 3)
        resListActions6 = Connection.getUserActions(username=TestDB.testUserName, active=False)
        # Delete all actions
        resDelete1 = Connection.deleteAction(actionId1)
        resDelete2 = Connection.deleteAction(actionId2)

        assert(actionId1 != None)
        assert(actionId2 != None)
        assert(len(resListActions1) == 2)
        assert(len(resListActions2) == 2)
        assert(len(resListActions3) == 1)
        assert(len(resListActions4) == 2)
        assert(len(resListActions5) == 0)
        assert(len(resListActions6) == 2)
        assert(resComplete)
        assert(not resCompleteNotexisting)
        assert(not resCancelNonexisting)
        assert(resCancel)
        assert(resDelete1)
        assert(resDelete2)

    def testClenup(seft):
        # Remove test user
        res = False
        id = Connection.getUserIdByName(TestDB.testUserName)
        if (dbFound(id)):
            res = Connection.deleteUser(id)
        # Close connection
        Connection.closeConnection()
        assert(res)

