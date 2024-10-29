import paho.mqtt.client as mqtt
import os
import random
import json
import queue
import time
from logger import log

STATUS_TOPIC="status"
COMMAND_TOPIC="commands"
DATA_TOPIC="data"

DAQ_PI_ID = os.getenv("DAQ_PI_ID")
BROKER_PORT = 1883

if not DAQ_PI_ID:
    log("DAQ_PI_ID not set in mqtt.py. Should be fixed (ENV not propagating from main.py?)")
    DAQ_PI_ID="invalid_id"

client = mqtt.Client(client_id=DAQ_PI_ID, clean_session=False)

lwt_payload = {"id": DAQ_PI_ID, "status": "offline"}
client.will_set(STATUS_TOPIC, payload=json.dumps(lwt_payload), qos=2, retain=True)

mqtt_queue = queue.Queue()
handle_message_fn = None

def run_connection(ip_address, handle_message):
    global handle_message_fn

    handle_message_fn = handle_message
    log("Starting MQTT thread...")
    client.connect(ip_address, BROKER_PORT, keepalive=5)
    client.on_connect = on_connect
    # client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.loop_start()  # Start MQTT loop in the background
    client.reconnect_delay_set(min_delay= 1, max_delay= 2)

    while True:
        try:
            # log("Waiting for message to send...")
            # Get the next message from the queue
            msg = mqtt_queue.get()  # This will block until a message is available
            topic, payload = msg
            client.publish(topic, payload, qos=0)
            # log(f"Published to {topic}: {payload}")
            mqtt_queue.task_done()  # Mark the task as done
        except Exception as e:
            log(f"Error in MQTT thread: {e}")

def send_data(message):
    mqtt_queue.put((DATA_TOPIC, message))

def disconnect():
    client.publish(STATUS_TOPIC, json.dumps(lwt_payload), qos=2)
    client.disconnect()

# MQTT event listeners
def on_connect(client, userdata, flags, rc):
    global connected
    connected = True
    log(f"Connected to MQTT broker with result code {rc}")
    client.subscribe(COMMAND_TOPIC, qos=1)
    payload = {"id": DAQ_PI_ID, "status": "online"}
    client.publish(STATUS_TOPIC, json.dumps(payload), qos=1)


def on_disconnect(client, userdata, rc):
    global connected
    connected = False
    log(f"Disconnected from MQTT broker! Result code: {rc}")

    while not connected:
        time.sleep(1)
        log("Attempting to reconnect...")
        client.reconnect()

def on_message(client, userdata, msg):
    print(f"Received message from topic '{msg.topic}': {msg.payload.decode()}")
    log(f"Received message from topic '{msg.topic}': {msg.payload.decode()}")

    if msg.topic == COMMAND_TOPIC:
        data = json.loads(msg.payload.decode())

        # get initial status of PIs
        if data["command"] == "get_status":
            payload = {"id": DAQ_PI_ID, "status": "online"}
            client.publish(STATUS_TOPIC, json.dumps(payload), qos=1)
            return

        if not handle_message_fn:
            log("WARNINIG: No message handler is set but a message was received")
            return

        handle_message_fn(data)
