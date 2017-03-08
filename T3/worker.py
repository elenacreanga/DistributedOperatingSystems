import os
import stat
import time
import hashlib
import random
import win32net

USERNAME = 'bob'
PASSWORD = ''

USE_DICT = {}
USE_DICT['remote'] = '\\\\MACBOOKPRO-AE22\\Tema3'
USE_DICT['password'] = PASSWORD
USE_DICT['username'] = USERNAME
win32net.NetUseAdd(None, 2, USE_DICT)

ROOT_FOLDER = r'\\MACBOOKPRO-AE22\Tema3\\'
COMPUTER_NAME = os.environ['COMPUTERNAME']
ELECTIONS_FOLDER = ROOT_FOLDER + "Elections\\"
READY_WORKERS_FOLDER = ROOT_FOLDER + "ReadyWorkers\\"
TASKS_FOLDER = ROOT_FOLDER + "Tasks\\"
FINISHED_TASKS_FOLDER = ROOT_FOLDER + "FinishedTasks\\"
TASKS_TO_DO = ROOT_FOLDER + "TasksToDo\\"
WORKERS_FOLDER = ROOT_FOLDER + "Workers\\"
print("[COMPUTERNAME] " + COMPUTER_NAME)

def check_if_folder_exists(directory):
    """ check if folder exists and if not create it """
    directory_path = directory
    if not os.path.isdir(directory_path):
        os.makedirs(directory_path, mode=0o777)

def touch(file_path):
    """ method for crating a file """
    open(file_path, 'w').close()

def write_to_file(file_path, text):
    """ method for writing into a file """
    path = file_path
    file = os.open(path, os.O_CREAT|os.O_RDWR, stat.S_IRWXO|stat.S_IRWXG|stat.S_IRWXU)
    os.write(file, text)
    os.close()

def get_file_content(file_path):
    """ read the content of a file """
    with open(file_path) as file:
        return file.read()

def diff(first, second):
    """ get all available workers """
    second = set(second)
    return [item for item in first if item not in second]

def add_worker_to_queue():
    """this adds the current computer to the queue"""
    print("[add_worker_to_queue] => Adding computer to queue")
    check_if_folder_exists(READY_WORKERS_FOLDER)
    touch(READY_WORKERS_FOLDER + COMPUTER_NAME)
    print("[add_worker_to_queue] => " + COMPUTER_NAME + " joined")

def wait_for_workers_to_join(election_start):
    """ wait until more participants join """
    print("[wait_for_workers_to_join] Waiting for workers to join")
    check_if_folder_exists(READY_WORKERS_FOLDER)
    current_ready_workers_count = len(os.listdir(READY_WORKERS_FOLDER))
    is_election_file_created = os.path.isfile(election_start)

    while current_ready_workers_count < 2 and (not is_election_file_created):
        print("[wait_for_workers_to_join] Waiting for workers to join")
        time.sleep(10)
        current_ready_workers_count = len(os.listdir(READY_WORKERS_FOLDER))
        is_election_file_created = os.path.isfile(election_start)

def prepare_to_elect_master(election_start):
    """ prepare elections """
    print("Preparing to elect master")
    if not os.path.isfile(election_start):
        try:
            touch(election_start)
        except Exception:
            print("[prepare_to_elect_master] => StartElections already created")
    os.remove(READY_WORKERS_FOLDER + COMPUTER_NAME)
    touch(ELECTIONS_FOLDER + COMPUTER_NAME)
    time.sleep(20)

def begin_elections():
    """ begin elections """
    candidates = os.listdir(ELECTIONS_FOLDER)
    candidates.remove("StartElections")
    if os.path.exists(ELECTIONS_FOLDER + ".DS_Store"):
        candidates.remove(".DS_Store")
    election_restart_file = "RestartElections"
    if os.path.exists(ELECTIONS_FOLDER + election_restart_file):
        candidates.remove("RestartElections")
    candidates.sort(reverse=True)
    if not os.path.isfile(ELECTIONS_FOLDER + "ElectionResults.txt"):
        try:
            write_to_file(ELECTIONS_FOLDER + "ElectionResults.txt", "\r\n".join(candidates))
        except:
            print("[begin_elections] => ElectionResults.txt already created")
    time.sleep(2)
    os.remove(ELECTIONS_FOLDER + COMPUTER_NAME)
    print("Elections ended")

def is_master():
    """ check if current computer is master or worker """
    election_results = get_file_content(ELECTIONS_FOLDER + "ElectionResults.txt")
    return election_results.startswith(COMPUTER_NAME)

def get_tasks_in_progress():
    """ get the work in progress """
    work_in_progress = dict()
    check_if_folder_exists(TASKS_FOLDER)
    for file in os.listdir(TASKS_FOLDER):
        try:
            work_in_progress[get_file_content(TASKS_FOLDER + file)] = file
        except:
            print("[get_tasks_in_progress] Worker " + file + " just finished a task")
    return work_in_progress

def get_finished_tasks():
    """ get finished tasks """
    tasks_finished = dict()
    check_if_folder_exists(FINISHED_TASKS_FOLDER)
    for file in os.listdir(FINISHED_TASKS_FOLDER):
        content = ""
        try:
            content = get_file_content(FINISHED_TASKS_FOLDER + file)
        except:
            print("[get_finished_tasks] => Worker " + file + " is reporting new task done")
        for line in content.split("\r\n"):
            parts = line.split("=>")
            if len(parts) > 1:
                tasks_finished[parts[0]] = parts[1]
    return tasks_finished

def get_remaining_tasks(finished_tasks, tasks_in_progress):
    """ get remaining tasks """
    remaining_tasks = []
    check_if_folder_exists(TASKS_TO_DO)
    for file in os.listdir(TASKS_TO_DO):
        if (not file in finished_tasks) and (not file in tasks_in_progress):
            remaining_tasks.append(file)
    return remaining_tasks

def get_workers_list():
    """ get the list of workers """
    all_workers = os.listdir(WORKERS_FOLDER)
    busy_workers = os.listdir(TASKS_FOLDER)
    return diff(all_workers, busy_workers)

def assign_task_to_worker(task, worker):
    """ assign a task to a worker """
    print("[assign_task_to_worker] => Task " + task + " is now assigned to worker " + worker)
    try:
        write_to_file(TASKS_FOLDER + worker, task)
    except:
        print("[assign_task_to_worker] Task " + task + " not assigned to " + worker)

def kill_worker(worker):
    """ kill worker """
    print("[kill_worker] Killing Worker => " + worker)
    try:
        if os.path.isfile(WORKERS_FOLDER + worker):
            os.remove(WORKERS_FOLDER + worker)
        if os.path.isfile(TASKS_FOLDER + worker):
            os.remove(TASKS_FOLDER + worker)
        if os.path.isfile(ELECTIONS_FOLDER + "RestartElections\\" + worker):
            os.remove(ELECTIONS_FOLDER + "RestartElections\\" + worker)
    except:
        print("[kill_worker] " + worker + " worker killed with errors!")

def cleanup_workers():
    """ cleanup workers """
    for file in os.listdir(TASKS_FOLDER):
        last_altering = time.time()
        try:
            last_altering = os.path.getmtime(TASKS_FOLDER + file)
        except:
            print("[cleanup_workers] Worker " + file + " already finished task")
        if time.time() - last_altering > 50:
            kill_worker(file)

def is_election_restarted():
    """ check whether file RestartElections is in the folder or not """
    reelection_folder = "RestartElections\\"
    check_if_folder_exists(ELECTIONS_FOLDER + reelection_folder)
    return len(os.listdir(ELECTIONS_FOLDER + reelection_folder)) > 0

def run_master():
    """ run master """
    while True:
        tasks_in_progress = get_tasks_in_progress()
        finished_tasks = get_finished_tasks()
        remaining_tasks = get_remaining_tasks(finished_tasks, tasks_in_progress)

        if len(remaining_tasks) < 1:
            return True
        workers_list = get_workers_list()
        i = 0
        no_of_tasks = len(remaining_tasks)
        for worker in workers_list:
            assign_task_to_worker(remaining_tasks[i % no_of_tasks], worker)
            i = i + 1
        cleanup_workers()
        if is_election_restarted():
            return False

def get_assigned_task_for_worker(worker):
    """ get assigned task for worker """
    if os.path.isfile(TASKS_FOLDER + worker):
        try:
            return get_file_content(TASKS_FOLDER + worker)
        except:
            print("[get_assigned_task_for_worker] => Error reading assigned task for " + worker)
    return ""

def is_processing_finished():
    """ check if processing is done """
    tasks_in_progress = get_tasks_in_progress()
    finished_tasks = get_finished_tasks()
    remaining_tasks = get_remaining_tasks(finished_tasks, tasks_in_progress)
    return len(remaining_tasks) < 1

def process_file(file):
    """ create the md4 hash from task """
    md5 = hashlib.md5()
    for line in open(TASKS_TO_DO + file, "rb"):
        md5.update(line)
    return md5.hexdigest()

def execute_task(task):
    """ execute task from tasks to do and move to finished """
    print("[execute_task] => " + task)
    result = process_file(task)
    try:
        with open(FINISHED_TASKS_FOLDER + COMPUTER_NAME, "a") as file:
            file.write(task)
            file.write("=>")
            file.write(result)
            file.write("\r\n")
        os.remove(TASKS_FOLDER + COMPUTER_NAME)
    except:
        print("[execute_task] => Error reporting done work")

def run_worker():
    """ run worker """
    while True:
        time.sleep(1)
        task = get_assigned_task_for_worker(COMPUTER_NAME)
        start_waiting_time = time.time()
        while (len(task) == 0) and (time.time() - start_waiting_time < 40):
            task = get_assigned_task_for_worker(COMPUTER_NAME)
        print("[run_worker] => Assigned Task is " + task)
        if len(task) == 0:
            if is_processing_finished():
                return True
            return False

        execute_task(task)
        if is_election_restarted():
            return False

def restart_elections():
    """ restart elections """
    print("[restart_elections] => Elections Restarted!")
    touch(ELECTIONS_FOLDER + "RestartElections\\" + COMPUTER_NAME)
    if os.path.isfile(ELECTIONS_FOLDER + "StartElections"):
        try:
            os.remove(ELECTIONS_FOLDER + "StartElections")
        except:
            print("[restart_elections] => StartElections already removed")
    if os.path.isfile(ELECTIONS_FOLDER + "ElectionResults.txt"):
        try:
            os.remove(ELECTIONS_FOLDER + "ElectionResults.txt")
        except:
            print("[restart_elections] => ElectionResults.txt already removed")

    reelections_folder = ELECTIONS_FOLDER + "RestartElections\\"
    while len(os.listdir(reelections_folder)) < len(os.listdir(WORKERS_FOLDER)) * 0.6:
        time.sleep(1)
    kill_worker(COMPUTER_NAME)
    main()

def main():
    """ main """
    add_worker_to_queue()

    election_start_file = ELECTIONS_FOLDER + "StartElections"
    check_if_folder_exists(ELECTIONS_FOLDER)
    wait_for_workers_to_join(election_start_file)

    prepare_to_elect_master(election_start_file)
    begin_elections()

    if is_master():
        print("I am manager")
        result = run_master()
        if not result:
            restart_elections()
    else:
        print("I am worker " + COMPUTER_NAME)
        touch(WORKERS_FOLDER + COMPUTER_NAME)
        result = run_worker()
        if not result:
            restart_elections()
    # Add to Worker queue
    # Make elections from all workers
    # Check whether master or slave
    # If master - proceed assigning tasks
    # if slave - get ready mark myself available
    #   process tasks
    #     # if result is false on any, rerun elections

main()
