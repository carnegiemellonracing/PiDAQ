import random
import socketio
import time
sio = socketio.Client()

running_tests = []

@sio.event
def connect():
  sio.emit('join_room',{"room":"rasppi","currRoom":""})
  print("connection established")


@sio.on('message')
def message(data):
    print('Received data: ', data)

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

@sio.on('stop_test')
def stop_test(test_name):
  if test_name in running_tests:
    running_tests.remove(test_name)
    print(f"stopped test \"{test_name}\"")

def run_test(test_name):
  idv = 0
  dv = 0
  while idv < 100 and test_name in running_tests:
    dv = random.randint(1, 101)
    idv += 1
    print(f"data: {idv, dv}, sender: {sio.sid}")
    
    
    sio.emit("test_data",{"testName":test_name, "data":[idv, dv], "sender":sio.sid})
    time.sleep(0.5)

sio.connect('http://127.0.0.1:3001')
sio.wait()
