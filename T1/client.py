import os, time, getpass, win32api, datetime
import sys, traceback, types
import win32api
import win32net

userName= os.environ['COMPUTERNAME']
limit=0.9

ip = '//MACBOOKPRO-AE22'
username = 'Guest'
password = ''

use_dict={}
use_dict['remote']='\\\\MACBOOKPRO-AE22\\SyncFolder'
use_dict['password']=password
use_dict['username']=username
win32net.NetUseAdd(None, 2, use_dict)

queryFolderPath='//MACBOOKPRO-AE22/SyncFolder/ServerFiles'
answerPath='//MACBOOKPRO-AE22/SyncFolder/ClientFiles/answer_'+userName+'.txt'
queryPath='//MACBOOKPRO-AE22/SyncFolder/ServerFiles/query_'+userName+'.txt'

def touch(filePath):
	currentTime = time.time()
	if not os.path.exists(queryFolderPath):
		print("did make folder")
		os.makedirs(os.path.dirname(queryFolderPath))

	print("fpath " + filePath)
	open(filePath, "w").close()
	return currentTime

def clientOperations():
	t1=touch(queryPath)
	time.sleep(0.3)

	print("t1 " + str(t1))
	print("anspath " + answerPath)
	while(os.path.exists(answerPath)==False):
		time.sleep(0.3)

	t3 = time.time()
	f=open(answerPath,'r')
	serverTime=f.readline()
	print("server time " + str(serverTime))
	f.close()

	delta=(t3-t1)/2
	print("delta " + str(delta))
	timeToSet = datetime.datetime.utcfromtimestamp(float(serverTime)+delta)

	print('time to set on client')
	print(timeToSet)

	win32api.SetSystemTime(timeToSet.year,timeToSet.month,timeToSet.day,timeToSet.day,timeToSet.hour,timeToSet.minute,int(timeToSet.second),int(timeToSet.microsecond/1000))

	os.remove(answerPath)
	timeToSetAsFloat=float(serverTime)+delta

	return timeToSetAsFloat

def main():
	timeToSet=clientOperations()
	delta= time.time()-timeToSet

	while (abs(delta)>limit):
		print('delta='+ str(abs(delta)))

		timeToSet=clientOperations()
		delta= time.time()-timeToSet

main()
