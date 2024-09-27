import random
import socketio
import time
sio = socketio.Client()

running_tests = []

#testing vars
rpiID = f"rpi{random.randint(1000,10000)}" # replace with env variables
numData = 100
freq = 10 #sometimes miss the first few data points with high freq (eg 1000Hz). otherwise get all values

@sio.event
def connect():
  sio.emit('join_rpi',{"env":rpiID})
  print("connection established")

@sio.event
def connect_error(data):
    print("The connection failed")

@sio.event
def disconnect():
    print("Disconnected from server")
  
@sio.on('start_test')
def start_test(test_name):
  print(f"starting test \"{test_name}\"")
  running_tests.append(test_name)
  run_test(test_name)

@sio.on('stop_test_rpi')
def stop_test(test_name):
  if test_name in running_tests:
    running_tests.remove(test_name)
    print(f"stopped test \"{test_name}\"")

def run_test(test_name):
  idv = 0
  dv = 0
  while idv < numData and test_name in running_tests:
    dv = random.randint(1, 100)
    idv += 1
    print(f"data: {idv, dv}, sender: {rpiID}")
    
    
    sio.emit("test_data",{"testName":test_name, "data":[idv, dv], })
    time.sleep(1/freq)
  
  sio.emit("stop_test_server",{"testName":test_name})

sio.connect('http://127.0.0.1:3001')
sio.wait()
