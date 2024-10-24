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
const brokerUrl = 'mqtt://test.mosquitto.org';
mqtt_client = mqtt.connect(brokerUrl);
const commandTopic = 'command_stream';
const dataTopic = 'data_stream';

// Test data state manager
const allRPI = {};
const allData = {}; // To store all test data
let runningTest = "";
const connectedPis = [];


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

  // RPi to WSS: connection message
  // joing "rpi" room in SIO
  socket.on("join_rpi", (data) => {
    const id = socket.id;
    const pi_ID = data.pi_ID;
    allRPI[id] = pi_ID;

    socket.join("rpi");

    if (!connectedPis.includes(pi_ID)) {
      console.log(`RPI ${socket.id} has joined. pi_ID: ${pi_ID}`);
      // Tell *this* raspberry pi to stop all tests
      msg = { "command": "stop" };
      mqtt_client.publish(commandTopic, JSON.stringify(msg), { qos: 1 });
    } else {
      console.log(`RPI ${socket.id} has reconnected. pi_ID: ${pi_ID}`);
      if (!runningTest) {
        msg = { "command": "stop" };
        mqtt_client.publish(commandTopic, JSON.stringify(msg), { qos: 1 });
      }
    }
    connectedPis.push(pi_ID);

    io.to("client").emit("status_rpis", allRPI);
  });

  // Frontend to WSS: connection message
  // adds this webclient to "client" room
  socket.on("join_client", () => {
    socket.join("client");
    console.log(`Client ${socket.id} has joined`);

    // Send the current allData to the client
    io.to("client").emit("status_rpis", allRPI);
    io.to("client").emit("status_test", runningTest);
    io.to("client").emit("all_data", allData);
  });

  // socket disconnect handler
  socket.on("disconnect", () => {
    if (socket.id in allRPI) {
      console.log(`RPI ${allRPI[socket.id]} disconnected`);
      delete allRPI[socket.id];
      io.to("client").emit("status_rpis", allRPI);
    } else {
      console.log(`Client ${socket.id} has disconnected`);
    }
  });

  socket.on("disconnecting", () => {
    console.log(`User ${socket.id} disconnecting`);
  });

  socket.on("connect_error", () => {
    console.log(`User ${socket.id} had connection error`);
  });


  // Frontend to WSS: start test message
  // tells all connected Pis to start collecting data
  socket.on("start_test", (data) => {
    console.log("starting test");
    if (runningTest) return;
    const timeStamp = Date.now();
    const testName = `${data.testName}---${timeStamp}`;

    allData[testName] = {
      info: {
        time: timeStamp,
        name: data.testName,
        senders: [],
      },
      data: {},
    };

    console.log(`Starting test "${testName}"`);
    runningTest = testName;

    message = { "command": "start", "test_name": runningTest };
    mqtt_client.publish(commandTopic, JSON.stringify(message), { qos: 1 });

    io.to("client").emit("all_data", allData);
  });

  // Frontend to WSS: test stop messages
  // tells all connected Pis to stop collecting data
  socket.on("stop_test_server", (data) => {
    const testName = data.testName;

    if (runningTest == testName) {
      console.log(`Stopping test "${testName}"`);
      message = { "command": "start", "test_name": runningTest };
      mqtt_client.publish(commandTopic, JSON.stringify(message), { qos: 1 });
      runningTest = null;

      io.to("client").emit("status_test", runningTest);
    } else {
      console.log(`Error: Test "${testName}" is not running`);
    }
  });

  // returns the status of the current test
  socket.on("get_tests", () => {
    io.to("client").emit("status_test", runningTest);
  });

  // RPi to WSS: test data push
  // forwards test data from Pi to web clients
  // socket.on("test_data", (data) => {
  //   const { testName, data: test_data } = data;
  //   const sender = allRPI[socket.id];

  //   const average_temp = test_data.tire_temp_frame
  //     ? test_data.tire_temp_frame.reduce((acc, v) => {
  //       return acc + v;
  //     }, 0) / test_data.tire_temp_frame.length
  //     : false;

  //   test_data["average_temp"] = average_temp;

  //   if (allData[testName]) {
  //     if (!allData[testName]["info"]["senders"].includes(sender)) {
  //       allData[testName]["info"]["senders"].push(sender);
  //     }

  //     if (!allData[testName]["data"][sender]) {
  //       allData[testName]["data"][sender] = [];
  //     }
  //     allData[testName]["data"][sender].push(test_data);
  //   }

  //   io.to("client").emit("test_data", {
  //     testName,
  //     data: test_data,
  //     sender,
  //   });
  // });
});


// MQTT Client Stuff
// Topics for communication
mqtt_client.on('connect', () => {
  console.log('Connected to MQTT broker.');

  // Subscribe to command and sensor data stream topics
  mqtt_client.subscribe(commandTopic, { qos: 1 });
  mqtt_client.subscribe(dataTopic, { qos: 0 });
});

// Handle incoming messages from the subscribed topic
mqtt_client.on('message', (topic, message) => {
  console.log(`Received message from ${topic}: ${message.toString()}`);

  // Handle commands
  if (topic === dataTopic) {

    // parse test data as JSON
    const data = JSON.parse(message.toString());
    const { testName, data: test_data } = data;
    const sender = allRPI[socket.id];

    // calculate average temps
    const average_temp = test_data.tire_temp_frame
      ? test_data.tire_temp_frame.reduce((acc, v) => {
        return acc + v;
      }, 0) / test_data.tire_temp_frame.length
      : false;
    test_data["average_temp"] = average_temp;

    if (allData[testName]) {
      if (!allData[testName]["info"]["senders"].includes(sender)) {
        allData[testName]["info"]["senders"].push(sender);
      }

      if (!allData[testName]["data"][sender]) {
        allData[testName]["data"][sender] = [];
      }
      allData[testName]["data"][sender].push(test_data);
    }

    // broadcast to web clients
    io.to("client").emit("test_data", {
      testName,
      data: test_data,
      sender,
    });
  }
});

server.listen(WSS_PORT, () => {
  console.log("server is running");
});