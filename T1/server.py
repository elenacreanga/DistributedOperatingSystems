import os, time, glob, stat, datetime

answerPath='/BHD/SyncFolder/ClientFiles/'
queryPath='/BHD/SyncFolder/ServerFiles/'

queryPattern=queryPath+'query_*.txt'

def findFilesWithPattern():
	return glob.glob(queryPattern)

def writeTimeInFile(currentTime,clientName):
	tempFilePath=answerPath+'temp.txt'
	fans = os.open(tempFilePath, os.O_CREAT|os.O_RDWR, stat.S_IRWXO|stat.S_IRWXG|stat.S_IRWXU)
	os.write(fans, str(currentTime).encode())
	os.close(fans)
	answerFilePath=answerPath+'answer_'+clientName+'.txt'
	os.rename(tempFilePath,answerFilePath)

def main():
	if not os.path.exists(answerPath):
		os.makedirs(os.path.dirname(answerPath))

	filesWithPattern=findFilesWithPattern()

	while True:
		time.sleep(2)
		while (len(filesWithPattern)<1):
			filesWithPattern=findFilesWithPattern()

		for file in filesWithPattern:
			fileName=os.path.basename(file)
			time.sleep(1)
			os.remove(file)

			currentTime = time.time()

			print(datetime.datetime.fromtimestamp(currentTime))

			clientName = fileName[6:].split('.')[0]
			print('client name'+clientName)
			writeTimeInFile(currentTime,clientName)

		filesWithPattern=[]

main()
