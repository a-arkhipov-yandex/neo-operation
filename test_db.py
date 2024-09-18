from __future__ import annotations

import pytest

from datetime import datetime as dt, timedelta
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
        data = "123"
        resCorrectState = Connection.setUserState(TestDB.testUserName1, STATE_ACTIONTEXT, data)
        userInfo = Connection.getUserInfoByName(TestDB.testUserName1)
        assert(userInfo['state_data'] == data)
        assert(userInfo['state'] == STATE_ACTIONTEXT)
        resUserState2 = Connection.getUserState(TestDB.testUserName1)
        resClearUserState = Connection.clearUserState(TestDB.testUserName1)
        userInfo = Connection.getUserInfoByName(TestDB.testUserName1)
        assert(userInfo['state_data'] == None)
        assert(userInfo['state'] == None)
        resUserState3 = Connection.getUserState(TestDB.testUserName1)
        res11 = Connection.getUserIdByName(testIncorrectUserName1)
        res2 = Connection.addUser(testIncorrectUserName2,1)
        res3 = Connection.addUser(testIncorrectUserName3,1)
        res4 = Connection.getUserIdByName('nonexisting_user')
        assert(not res1)
        assert(resUserInfo1 and len(resUserInfo1) == 5)
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
        newTitle = "newT"
        usename1 = TestDB.testUserName1
        resRemWithWithout = Connection.getActions(username=usename1, withoutReminders=True, withReminders=True)
        assert(resRemWithWithout == False)
        resWithoutRem = Connection.getActions(username=usename1, withoutReminders=True)
        assert(len(resWithoutRem) == 1)
        resShown1 = Connection.getActions(username=usename1, withReminders=True, shown=True)
        assert(len(resShown1) == 0)
        Connection.setReminder(username=usename1, actionId=actionId1,reminder=dt.now()-timedelta(hours=10))
        resShown1 = Connection.getActions(username=usename1, withReminders=True, shown=True)
        assert(len(resShown1) == 0)
        resNoShown1 = Connection.getActions(username=usename1, withReminders=True)
        assert(len(resNoShown1) == 1)
        Connection.markReminderAsShown(username=usename1, actionId=actionId1)
        resShown1 = Connection.getActions(username=usename1, withReminders=True, shown=True)
        assert(len(resShown1) == 1)
        Connection.clearReminder(username=usename1, actionId=actionId1)
        resTitleChange = Connection.udpdateActionTitle(TestDB.testUserName1, actionId=actionId1, newTitle=newTitle)
        assert(resTitleChange)
        resTitleChange = Connection.udpdateActionTitle(TestDB.testUserName1, actionId=actionId1+100, newTitle=newTitle)
        assert(resTitleChange == False)
        logsUpdated = Connection.getLogs(actionId=actionId1, logType=LOGTYPE_TITLEUPDATED)
        assert(len(logsUpdated) > 0)
        newText = "newT"
        resAddText = Connection.udpdateActionText(TestDB.testUserName1, actionId=actionId1, addText=newText)
        assert(resAddText)
        resAddText = Connection.udpdateActionText(TestDB.testUserName1, actionId=actionId1+100, addText=newText)
        assert(resAddText == False)
        logsAdded = Connection.getLogs(actionId=actionId1, logType=LOGTYPE_TEXTADDED)
        assert(len(logsAdded) > 0)
        actionInfo1 = Connection.getActionInfo(TestDB.testUserName1, actionId=actionId1)
        assert(actionInfo1['title'] == newTitle)
        assert(newText in actionInfo1['text'])
        logsCreated = Connection.getLogs(actionId=actionId1,logType=LOGTYPE_CREATED)
        resReminder1 = Connection.getReminder(TestDB.testUserName1, actionId1) # None
        actionWithReminders1 = Connection.getActionsWithExpiredReminders(username=TestDB.testUserName1)
        resActionWithReminders1 = (len(actionWithReminders1) == 0)
        resSetReminderCorrect = Connection.setReminder(TestDB.testUserName1, actionId1, dt.now()) # True
        resSetReminderInCorrect = Connection.setReminder(TestDB.testUserName1, actionId1, "20.sd12.d2024") # True
        resReminder2 = Connection.getReminder(TestDB.testUserName1, actionId1) # not None
        resLogCreated = (len(logsCreated) > 0)
        # Create action 2
        actionId2 = Connection.addAction(TestDB.testUserName2,'Test action 2','Test test 2','')
        actionId3 = Connection.addAction(TestDB.testUserName2,'Test action 3','Test test 3','')
        searchActiveNonexistingAction = Connection.searchActions('test2323', username=TestDB.testUserName2)
        assert(len(searchActiveNonexistingAction) == 0)
        searchAllNonexistingAction = Connection.searchActions('test2323', username=TestDB.testUserName2)
        assert(len(searchAllNonexistingAction) == 0)
        searchActiveExistingActionTitle = Connection.searchActions('action 2', username=TestDB.testUserName2)
        assert(len(searchActiveExistingActionTitle) == 1)
        searchAllExistingActionTitle = Connection.searchActions('action', username=TestDB.testUserName2)
        assert(len(searchAllExistingActionTitle) == 2)
        searchActiveExistingActionText = Connection.searchActions('test 2', username=TestDB.testUserName2)
        assert(len(searchActiveExistingActionText) == 1)
        searchAllExistingActionText = Connection.searchActions('Test test', username=TestDB.testUserName2)
        assert(len(searchAllExistingActionText) == 2)
        oneHour = timedelta(hours=1)
        Connection.setReminder(TestDB.testUserName2, actionId3, dt.now()-oneHour) # True
        Connection.setReminder(TestDB.testUserName2, actionId2, "20.12.2034") # True
        actionsWithReminders2 = Connection.getActionsWithExpiredReminders(username=TestDB.testUserName2)
        Connection.deleteAction(actionId3)
        # Get list of active actions (must be 1)
        resListActions1 = Connection.getActions(username=TestDB.testUserName1, active=True)
        # Get list of all actions (must be 1)
        resListActions2 = Connection.getActions(username=TestDB.testUserName2, active=False)
        # Get list of all actions of all users (must be 2)
        resListActionsAllUsers1 = Connection.getActions(active=False)
        # Complete action 1
        resCompleteActionWrongUser = Connection.completeAction(username=TestDB.testUserName2, actionId=actionId1)
        resComplete = Connection.completeAction(username=TestDB.testUserName1, actionId=actionId1)
        resReminderCompleted = Connection.getReminder(TestDB.testUserName1, actionId1) # None
        resSetReminderNotActive1 = Connection.setReminder(TestDB.testUserName1, actionId1, dt.now()) # True
        logsComplete = Connection.getLogs(actionId=actionId1,logType=LOGTYPE_COMPLETED)
        resLogComplete = (len(logsComplete) > 0)
        resCompleteNotexisting = Connection.completeAction(username=TestDB.testUserName1, actionId=1000000)
        # Get list of active actions (must be 0)
        resListActions3 = Connection.getActions(username=TestDB.testUserName1, active=True)
        # Get list of all actions (must be 1)
        resListActions4 = Connection.getActions(username=TestDB.testUserName1, active=False)
        # Cancel action 2
        resCancelActionWrongUser = Connection.completeAction(username=TestDB.testUserName1, actionId=actionId2)
        resActivated = Connection.getActions(username=usename1, active=True)
        assert(len(resActivated) == 0)
        resActivate1 = Connection.activateAction(actionId=actionId1,username=usename1)
        assert(resActivate1)
        resActivated = Connection.getActions(username=usename1, active=True)
        assert(len(resActivated) == 1)
        resChangeStatus = Connection.changeActionStatus(actionId=actionId1, status=1000)
        assert(resChangeStatus == False)
        resChangeStatus = Connection.changeActionStatus(actionId=actionId1+100, status=ACTION_ACTIVE)
        assert(resChangeStatus == False)
        resChangeStatus = Connection.changeActionStatus(actionId=actionId1, status=ACTION_ACTIVE)
        assert(resChangeStatus == False)
        resChangeStatus = Connection.changeActionStatus(actionId=actionId1, status=ACTION_COMPLETED)
        assert(resChangeStatus)
        resChangeStatus = Connection.changeActionStatus(actionId=actionId1, status=ACTION_CANCELLED)
        assert(resChangeStatus == False)
        resChangeStatus = Connection.changeActionStatus(actionId=actionId1, status=ACTION_ACTIVE)
        resComplete = Connection.completeAction(username=TestDB.testUserName1, actionId=actionId1)
        resCancel = Connection.cancelAction(username=TestDB.testUserName2, actionId=actionId2)
        resReminderCancelled = Connection.getReminder(TestDB.testUserName2, actionId2) # None
        resSetReminderNotActive2 = Connection.setReminder(TestDB.testUserName2, actionId2, dt.now()) # True
        logsCancelled = Connection.getLogs(actionId=actionId1,logType=LOGTYPE_CREATED)
        resLogCancelled = (len(logsCancelled) > 0)
        resCancelNonexisting = Connection.cancelAction(username=TestDB.testUserName1, actionId=100000000)
        # Get list of active actions (must be 0)
        resListActions5 = Connection.getActions(username=TestDB.testUserName2, active=True)
        # Get list of all actions (must be 1)
        resListActions6 = Connection.getActions(username=TestDB.testUserName2, active=False)
        resListActionsAllUsers2 = Connection.getActions(active=False)
        # Delete all logs and actions
        resDelete1 = Connection.deleteAction(actionId1)
        resDelete2 = Connection.deleteAction(actionId2)

        assert(actionId1 != None)
        assert(actionId2 != None)
        assert(resReminder1 == None)
        assert(resReminderCompleted == None)
        assert(resReminderCancelled == None)
        assert(resSetReminderCorrect == True)
        assert(resReminder2 != None)
        assert(resSetReminderInCorrect == False)
        assert(resActionWithReminders1)
        assert(len(actionsWithReminders2) == 1)
        assert(resSetReminderNotActive1 == False)
        assert(resSetReminderNotActive2 == False)
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
        assert(resDelete1)
        assert(resDelete2)

    def testReminders(self):
        usename = TestDB.testUserName1
        # Create action 1
        aId1 = Connection.addAction(username=usename,title="t1",text="text1",fromTxt=None)
        assert(aId1)
        buttons = "19239232343"
        ret = Connection.udpdateActionButtons(username=usename,actionId=aId1,buttons=buttons)
        assert(ret)
        ret = Connection.udpdateActionButtons(username='nonexistingusename',actionId=aId1,buttons=buttons)
        assert(not ret)
        ret = Connection.udpdateActionButtons(username=usename,actionId=aId1+100,buttons=buttons)
        assert(not ret)
        actionInfo = Connection.getActionInfo(username=usename,actionId=aId1)
        assert(actionInfo['buttons'] == buttons)
        ret = Connection.clearActionButtons(username=usename,actionId=aId1)
        assert(ret)
        actionInfo = Connection.getActionInfo(username=usename,actionId=aId1)
        assert(actionInfo['buttons'] == None)
        # Create action 2
        aId2 = Connection.addAction(username=usename,title="t2",text="text2",fromTxt=None)
        assert(aId2)
        # Show actions with expired reminders not shown - 0
        exNotShown = Connection.getActionsWithExpiredReminders(username=usename)
        assert(len(exNotShown) == 0)
        # Show actions with expired reminders shown - 0
        exShown = Connection.getActionsWithShownExpiredReminders(username=usename)
        assert(len(exShown) == 0)
        # Set reminder to the 1 day ago
        diff = timedelta(days=1)
        setRem = Connection.setReminder(username=usename, actionId=aId1,reminder=dt.now()-diff)
        assert(setRem)
        # Show actions with expired reminders not shown - 1
        exNotShown = Connection.getActionsWithExpiredReminders(username=usename)
        assert(len(exNotShown) == 1)
        # Show actions with expired reminders shown - 0
        exShown = Connection.getActionsWithShownExpiredReminders(username=usename)
        assert(len(exShown) == 0)
        # Mark reminder as shown
        markRem = Connection.markReminderAsShown(username=usename, actionId=aId1)
        assert(markRem)
        # Show actions with expired reminders not shown - 0
        exNotShown = Connection.getActionsWithExpiredReminders(username=usename)
        assert(len(exNotShown) == 0)
        # Show actions with expired reminders shown - 1
        exShown = Connection.getActionsWithShownExpiredReminders(username=usename)
        assert(len(exShown) == 1)
        # Move reminder to 1 hours ago
        diff = timedelta(hours=3)
        setRem = Connection.setReminder(username=usename, actionId=aId1,reminder=dt.now()-diff)
        assert(setRem)
        # Show actions with expired reminders not shown - 1
        exNotShown = Connection.getActionsWithExpiredReminders(username=usename)
        assert(len(exNotShown) == 1)
        # Show actions with expired reminders shown - 1
        exShown = Connection.getActionsWithShownExpiredReminders(username=usename)
        assert(len(exShown) == 0)
        # Mark action completed
        resCom = Connection.completeAction(username=usename,actionId=aId1)
        assert(resCom)
        # Show actions with expired reminders not shown - 0
        exNotShown = Connection.getActionsWithExpiredReminders(username=usename)
        assert(len(exNotShown) == 0)
        # Show actions with expired reminders shown - 0
        exShown = Connection.getActionsWithShownExpiredReminders(username=usename)
        assert(len(exShown) == 0)
        # Cleanup
        assert(Connection.deleteAction(aId2))
        assert(Connection.deleteAction(aId1))

    def testClenup(seft):
        # Remove test user
        resDelete1 = False
        resDelete2 = False
        actionsUser1 = Connection.getActions(username=TestDB.testUserName1)
        for action in actionsUser1:
            id = action['id']
            Connection.deleteAction(id)
        actionsUser2 = Connection.getActions(username=TestDB.testUserName2)
        for action in actionsUser2:
            id = action['id']
            Connection.deleteAction(id)
        resDelete1 = Connection.deleteUser(TestDB.testUserId1)
        resDelete2 = Connection.deleteUser(TestDB.testUserId2)
        # Close connection
        Connection.closeConnection()
        assert(resDelete1)
        assert(resDelete2)

