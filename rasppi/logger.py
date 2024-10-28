import datetime
import sys
import atexit

def log(msg):
    print(f"[{datetime.datetime.now()}] {msg}")
    sys.stdout.flush()

def cleanup():
    sys.stdout.close()
    sys.stderr.close()

def log_to_file(filename):
    log_file = open(filename, "w", buffering=1)
    sys.stdout = log_file
    sys.stderr = log_file

atexit.register(cleanup)
