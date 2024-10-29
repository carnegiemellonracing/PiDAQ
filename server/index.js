import express from "express";
import { createServer } from "http";
import cors from "cors";
import { Server } from "socket.io";
import mqtt from "mqtt";

// SocketIO WSS setup
const app = express();
app.use(cors());
const server = createServer(app);
const io = new Server(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"],
  },
  pingInterval: 1000,
  pingTimeout: 3000,
});
const WSS_PORT = 3001;

// MQTT Setup
const brokerUrl = "mqtt://localhost";
const mqtt_client = mqtt.connect(brokerUrl);
const COMMAND_TOPIC = "commands";
const DATA_TOPIC = "data";
const STATUS_TOPIC = "status";

// Test data state manager
class ServerStateManager {
  constructor() {
    this.connectedPis = new Set();
    this.testData = {};
    this.runningTest = "";
  }

  // returns list of all connected Pis
  getPis() {
    return this.connectedPis;
  }

  getPisAsArray() {
    return Array.from(this.getPis());
  }

  // adds a pi to the list of connected Pis
  addPi(id) {
    this.connectedPis.add(id);
  }

  // removes a pi to the list of connected Pis
  removePi(id) {
    this.connectedPis.delete(id);
  }

  removeAllPis() {
    this.connectedPis.clear();
  }

  // start a new test
  startTest(testName) {
    // create entry in testDate
    const timeStamp = Date.now();

    // update running test
    this.runningTest = `${testName}---${timeStamp}`;

    this.testData[this.runningTest] = {
      info: {
        time: timeStamp,
        name: this.runningTest,
        senders: [],
      },
      data: {},
    };
  }

  // returns all test data
  getAllData() {
    return serverState.testData;
  }

  // add a data point
  addDataPoint({
    testName: testName,
    name: name,
    value: value,
    pi_id: pi_id,
    timestamp: timestamp,
  }) {
    const testData = this.testData[testName];
    if (testData) {
      // if sender PiID is not in list of senders, add it
      if (!testData["info"]["senders"].includes(pi_id)) {
        testData["info"]["senders"].push(pi_id);
      }

      // if the data property doesn't contain the sender ID,
      // create a new array of data points
      if (!testData["data"][pi_id]) {
        testData["data"][pi_id] = {};
      }

      if (!testData["data"][pi_id][name]) {
        testData["data"][pi_id][name] = [];
      } else if (testData["data"][pi_id][name].length >= 100) {
        testData["data"][pi_id][name].shift();
      }

      // push your data point
      testData["data"][pi_id][name].push([timestamp, value]);
      // console.log(data);
    }
  }

  getTestName() {
    return this.runningTest;
  }

  stopTest(testName) {
    this.runningTest = "";
  }

  isTestRunning() {
    return !!this.runningTest;
  }
}

const serverState = new ServerStateManager();

// allData format:
// {
//     "testName---timeStamp": {
//         "info": {
//             "time": timeStamp,
//             "name": name,
//             "senders": ["rpi20", "rpi32"]
//         },
//         "data": {
//             "rpi20": [[1, 2], [2, 20]],
//             "rpi32": [[1, 23], [2, 2]]
//         }
//     }
// }

// Socket.io Stuff
// ROOMS AVAILABLE:
// - "client": for web clients
// - "rpi": for all (connected) rapsberry pis

io.on("connection", (socket) => {
  // Frontend to WSS: connection message
  // adds this webclient to "client" room
  socket.on("join_client", () => {
    socket.join("client");
    console.log(`Client ${socket.id} has joined`);

    const message = {
      command: "get_status",
    };
    mqtt_client.publish(COMMAND_TOPIC, JSON.stringify(message), { qos: 1 });

    // Send the current allData to the client
    io.to("client").emit("status_rpis", serverState.getPisAsArray());
    io.to("client").emit("status_test", serverState.getTestName());
    io.to("client").emit("all_data", serverState.getAllData());
  });

  // socket disconnect handler
  socket.on("disconnect", () => {
    console.log(`Client ${socket.id} has disconnected`);
  });

  socket.on("connect_error", () => {
    console.log(`User ${socket.id} had connection error`);
  });

  // Frontend to WSS: start test message
  // tells all connected Pis to start collecting data
  socket.on("start_test", (data) => {
    if (serverState.isTestRunning()) return;

    const testName = data.testName;
    serverState.startTest(testName);
    console.log(`Starting test "${testName}"`);

    // send command to MQTT clients
    const message = {
      command: "start",
      test_name: serverState.getTestName(),
    };
    mqtt_client.publish(COMMAND_TOPIC, JSON.stringify(message), { qos: 1 });

    io.to("client").emit("all_data", serverState.getAllData());
    io.to("client").emit("status_test", serverState.getTestName());
  });

  // Frontend to WSS: test stop messages
  // tells all connected Pis to stop collecting data
  socket.on("stop_test_server", (data) => {
    const testName = data.testName;
    if (serverState.getTestName() != testName) {
      console.error(`Error: Test "${testName}" is not running`);
      return;
    }

    console.log(`Stopping test "${testName}"`);

    // send command to MQTT clients
    const message = {
      command: "stop",
      test_name: serverState.getTestName(),
    };
    mqtt_client.publish(COMMAND_TOPIC, JSON.stringify(message), { qos: 1 });

    serverState.stopTest();
    io.to("client").emit("status_test", serverState.getTestName());
  });

  // returns the status of the current test
  socket.on("get_tests", () => {
    io.to("client").emit("status_test", serverState.getTestName());
  });
});

// MQTT Client Stuff
// Topics for communication
mqtt_client.on("connect", () => {
  console.log("Connected to MQTT broker.");

  // Request status of all connected Raspberry Pis
  const message = {
    command: "get_status",
  };
  mqtt_client.publish(COMMAND_TOPIC, JSON.stringify(message), { qos: 1 });

  // Subscribe to topics
  // mqtt_client.subscribe(COMMAND_TOPIC, { qos: 1 });
  mqtt_client.subscribe(DATA_TOPIC, { qos: 0 });
  mqtt_client.subscribe(STATUS_TOPIC, { qos: 1 });

  // If no test is running, stop all Raspberry Pis
  if (!serverState.isTestRunning()) {
    const message = {
      command: "stop",
      test_name: "",
    };
    mqtt_client.publish(COMMAND_TOPIC, JSON.stringify(message), { qos: 1 });
  }
});

mqtt_client.on("disconnect", () => {
  console.log("Disconnected from MQTT broker");
  // Remove all Raspberry Pis from the server state
  serverState.removeAllPis();
  io.to("client").emit("status_rpis", serverState.getPisAsArray());
});

// Handle incoming messages from the subscribed topic
mqtt_client.on("message", (topic, message) => {
  // console.log(`Received message from ${topic}: ${message.toString()}`);
  // Status messages
  if (topic === STATUS_TOPIC) {
    const data = JSON.parse(message.toString());
    const { id, status } = data;

    if (status === "online") serverState.addPi(id);
    if (status === "offline") serverState.removePi(id);

    io.to("client").emit("status_rpis", serverState.getPisAsArray());
  }

  // Sensor data
  if (topic === DATA_TOPIC) {
    console.log("received raw", message.toString());
    const data = message.toString().split("|");
    const [id, testName, timestamp, name, packedValue] = data;

    let value = JSON.parse(packedValue);

    if (typeof value === "string" && !isNaN(parseFloat(value))) {
      value = parseFloat(value);
    } else if (typeof value === "string" && !isNaN(parseInt(value))) {
      value = parseInt(value);
    }

    console.log("Received data ", [id, testName, timestamp, name, value]);

    // update server state
    serverState.addDataPoint({ testName, name, value, pi_id: id, timestamp });

    // broadcast to web clients
    io.to("client").emit("all_data", serverState.getAllData());
  }
});

server.listen(WSS_PORT, () => {
  console.log("server is running");
});

// Send messsage to stop previously running tests
