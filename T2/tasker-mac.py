import collections, os, stat, random, string, time, hashlib, sys

def getFileMD5(filePath):
	m = hashlib.md5()
	m.update(open(filePath,"rb").read())
	return m.hexdigest()

def createRemainingTasks():
	if not os.path.isfile(remainingTasksFile):
		with open(remainingTasksFile, 'w') as fout:
			fout.writelines(remainingTasks)
def takeFirstTask():
	with open(remainingTasksFile, 'r') as fin:
		data = fin.readlines()
	if len(data) == 0 and anyWorkersInProgress():
		print "Work done"
		touch(allWorkDoneFile)
		sys.exit()
	with open(remainingTasksFile, 'w') as fout:
		fout.writelines(data[1:])
	return data[0].rstrip()
def addBackRemainingTask(task):
	with open(remainingTasksFile, 'a') as fout:
		fout.write(task + "\n")

def createFiles():
	def createFile():
		seed = "1092384956781341341234656953214543219"
		seedLength = len(seed) - 1
		words = open("lorem.txt", "r").read().replace("\n", '').split()

		def fdata():
			start = random.randint(0, seedLength)
			rotate = random.randint(0, seedLength)
			a = collections.deque(words)
			b = collections.deque(seed)
			while True:
				yield ' '.join(list(a)[0:1024])
				a.rotate(int(b[start]))
				b.rotate(rotate)

		g = fdata()
		size = 10240
		N = 5
		fname = ''.join(random.choice(letters) for _ in range(N))
		path = os.path.join(sharedFolderPath, fname + ".txt")
		fh = open(path, 'w')
		while os.path.getsize(path) < size:
			fh.write(g.next())

	nbOfFiles = 1000
	alreadyPresent = len([name for name in os.listdir(sharedFolderPath) if os.path.isfile(os.path.join(sharedFolderPath, name)) and not name.startswith(giveMeWorkPrefix) and not name.startswith(toDoPrefix) and not name.startswith(resultsPrefix) and not name.startswith(leaderPrefix) and not name.startswith(doneWorkPrefix) and name != allResultsFilename and name != remainingTasksFilename])
	for num in range(alreadyPresent, nbOfFiles):
		createFile()

	createRemainingTasks()

def assumeLeaderPosition():
	print "I am Leader"
	os.remove(os.path.join(sharedFolderPath, giveMeWorkPrefix + username))
	touch(os.path.join(sharedFolderPath, leaderPrefix + username))
	while True:
		if workDone():
			print "Work done"
			sys.exit()
		elif not leaderExists():
			start()
		else:
			currentTime = time.time()
			readyForWork = [name[len(giveMeWorkPrefix):] for name in os.listdir(sharedFolderPath) if os.path.isfile(os.path.join(sharedFolderPath, name)) and name.startswith(giveMeWorkPrefix)]
			doneWorkers = [name[len(doneWorkPrefix):] for name in os.listdir(sharedFolderPath) if os.path.isfile(os.path.join(sharedFolderPath, name)) and name.startswith(doneWorkPrefix)]

			if len(doneWorkers) > 0:
				maxDelta = 0
				maxDoneWorker = None
				#choose the worker that was the slowest -> has the least amount of time until is considered dead
				for doneWorker in doneWorkers:
					if doneWorker in tasksInProgress:
						delta = currentTime - tasksInProgress[doneWorker][1]
						if delta > maxDelta:
							maxDelta = delta
							maxDoneWorker = doneWorker

				print 'Done worker:'+ doneWorker

				if not maxDoneWorker is None:
					print "Getting results from " + maxDoneWorker
					resultsFile = os.path.join(sharedFolderPath, resultsPrefix + maxDoneWorker)
					writeResultsToAllResultsFile(resultsFile)
					os.remove(resultsFile)
					os.remove(os.path.join(sharedFolderPath, doneWorkPrefix + maxDoneWorker))
					del tasksInProgress[maxDoneWorker]
					maxDoneWorker = None


			if len(readyForWork) > 0:
				workerUsername = readyForWork[0]
				os.remove(os.path.join(sharedFolderPath, giveMeWorkPrefix + workerUsername))
				work = takeFirstTask()

				print "Gave work to " + workerUsername
				tasksInProgress[workerUsername] = (work, currentTime)
				makeToDoFileFor(workerUsername, work)

			#verify the time the toDo file was created and if the client responded in time
			#if not consider it dead and put the work back in the remainingWork list
			tasksInProgressCopy = tasksInProgress.copy()
			for workerInProgress in tasksInProgressCopy:
				taskInProgress = tasksInProgressCopy[workerInProgress]
				if currentTime - taskInProgress[1] > maxTimeUntilDead:
					del tasksInProgress[workerInProgress]
					addBackRemainingTask(taskInProgress[0])

def assumeWorkerPosition():
	print "I am Worker"
	giveMeWorkFileCreationTime = time.time()
	while True:
		if workDone():
			print "Work done"
			sys.exit()
		elif not leaderExists():
			start()
		elif not isWork():
			print "Waiting for work"
			if time.time() - giveMeWorkFileCreationTime > maxTimeForLeaderToGiveWork:
				leaderFile = [name for name in os.listdir(sharedFolderPath) if os.path.isfile(os.path.join(sharedFolderPath, name)) and name.startswith(leaderPrefix)][0]
				os.remove(os.path.join(sharedFolderPath, leaderFile))

			time.sleep(sleepBeforeNextWorkCheck)
		else:
			toDoFile = os.path.join(sharedFolderPath, toDoPrefix + username)
			work = readWork(toDoFile)
			print "Working on " + work

			work = work.split(tasksDelimiter)

			startWork = work[0]
			endWork = work[1]

			results = []
			for workPart in list(map(chr, range(ord(startWork), ord(endWork)+1))):
				for name in os.listdir(sharedFolderPath):
					filePath = os.path.join(sharedFolderPath, name)
					if os.path.isfile(filePath) and name.startswith(workPart) and not name.startswith(giveMeWorkPrefix) and not name.startswith(toDoPrefix) and not name.startswith(resultsPrefix) and not name.startswith(leaderPrefix) and not name.startswith(doneWorkPrefix) and name != allResultsFilename and name != remainingTasksFilename:
						results.append((name, getFileMD5(filePath)))

			print "Done working on " + startWork + "->" + endWork
			os.remove(toDoFile)

			makeResultsFile(results)
			makeDoneWorkFile()
			makeGiveMeWorkFile()
			giveMeWorkFileCreationTime = time.time()

def readWork(toDoFile):
	f=open(toDoFile,'r')
	work=f.readline()
	f.close()
	return work

def isWork():
	return os.path.isfile(os.path.join(sharedFolderPath, toDoPrefix + username))

def enoughParticipants():
	return len([name for name in os.listdir(sharedFolderPath) if os.path.isfile(os.path.join(sharedFolderPath, name)) and name.startswith(giveMeWorkPrefix)]) >= neededParticipants

def anyWorkersInProgress():
	return len([name for name in os.listdir(sharedFolderPath) if os.path.isfile(os.path.join(sharedFolderPath, name)) and name.startswith(toDoPrefix)]) >= 0

def leaderExists():
	return len([name for name in os.listdir(sharedFolderPath) if os.path.isfile(os.path.join(sharedFolderPath, name)) and name.startswith(leaderPrefix)]) == 1

def workDone():
	return len([name for name in os.listdir(sharedFolderPath) if os.path.isfile(os.path.join(sharedFolderPath, name)) and name == allWorkDoneFilename]) == 1

def chooseLeader():
	if (not leaderExists() and min([name[len(giveMeWorkPrefix):] for name in os.listdir(sharedFolderPath) if os.path.isfile(os.path.join(sharedFolderPath, name)) and name.startswith(giveMeWorkPrefix)]) == username):
		assumeLeaderPosition()
	else:
		assumeWorkerPosition()

def waitForParticipants():
	while not enoughParticipants() and not leaderExists():
		print "Waiting for participants"
		time.sleep(sleepBeforeNextWorkCheck)

	print "Choosing leader"
	chooseLeader()

def touch(filePath):
	open(filePath, "w").close()

def writeTextInFile(filePath, text):
	print "Write text in file" + filePath
	file = os.open(filePath, os.O_CREAT|os.O_RDWR, stat.S_IRWXO|stat.S_IRWXG|stat.S_IRWXU)
	os.write(file, text)
	os.close(file)

def makeGiveMeWorkFile():
	touch(os.path.join(sharedFolderPath, giveMeWorkPrefix + username))

def makeDoneWorkFile():
	touch(os.path.join(sharedFolderPath, doneWorkPrefix + username))

def makeToDoFileFor(workerUsername, work):
	writeTextInFile(os.path.join(sharedFolderPath, toDoPrefix + workerUsername), work)

def makeResultsFile(results):
	with open(os.path.join(sharedFolderPath, resultsPrefix + username), 'w') as f:
		for fileAndHash in results:
			f.write("%s=%s\n" % (fileAndHash[0], fileAndHash[1]))

def writeResultsToAllResultsFile(resultsFile):
	with open(resultsFile) as f:
		lines = f.readlines()
		with open(allResultsFile, "a") as f1:
			f1.writelines(lines)

def start():
	print "Starting..."
	makeGiveMeWorkFile()
	waitForParticipants()

neededParticipants = 2
letters = string.ascii_lowercase
tasksDelimiter = "->"
remainingTasks = [(letters[i] + tasksDelimiter + letters[i+1] + "\n") for i in range(len(letters) - 1)]
tasksInProgress = {}
maxTimeUntilDead = 500
maxTimeForLeaderToGiveWork = 5
sleepBeforeNextWorkCheck = 0.3

giveMeWorkPrefix = "giveMeWork"
doneWorkPrefix = "doneWork"
resultsPrefix = "results"
toDoPrefix = "toDo"
leaderPrefix = "leader"
allWorkDoneFilename = "allWorkDone"
remainingTasksFilename = "remainingTasks.txt"
allResultsFilename = "allresults.txt"

username = '192-168-0-101'

sharedFolderPath = "/BHD/Tema2/"
allWorkDoneFile = sharedFolderPath + "/" + allWorkDoneFilename
remainingTasksFile = sharedFolderPath + "/" + remainingTasksFilename
allResultsFile = "/BHD/Tema2/" + allResultsFilename


createFiles()
start()
