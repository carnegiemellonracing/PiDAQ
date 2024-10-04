import express from "express";
const app = express();

import { createServer } from "http";
import cors from "cors";
app.use(cors());

import { Server } from "socket.io";

const allRPI = {};
const allData = {}; // To store all test data
let runningTest = "";
const previouslyConnectedPis = [];

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

const server = createServer(app);
const io = new Server(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"],
  },
  pingInterval: 1000,
  pingTimeout: 3000,
});

io.on("connection", (socket) => {
  socket.on("join_rpi", (data) => {
    const id = socket.id;
    const env = data.env;
    socket.join("rpi");
    allRPI[id] = env;
    if (!previouslyConnectedPis.includes(env)) {
      console.log(`RPI ${socket.id} has joined. ENV: ${env}`);
      // Tell *this* raspberry pi to stop all tests
      socket.emit("stop_test_rpi", {});
    } else {
      console.log(`RPI ${socket.id} has reconnected. ENV: ${env}`);
      if (!runningTest) {
        socket.emit("stop_test_rpi", {});
      }
    }
    previouslyConnectedPis.push(env);

    io.to("client").emit("status_rpis", allRPI);
  });

  socket.on("join_client", () => {
    socket.join("client");
    console.log(`Client ${socket.id} has joined`);

    // Send the current allData to the client
    io.to("client").emit("status_rpis", allRPI);
    io.to("client").emit("status_test", runningTest);
    io.to("client").emit("all_data", allData);
  });

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
    socket.to("rpi").emit("start_test", testName);
    io.to("client").emit("all_data", allData);
  });

  socket.on("stop_test_server", (data) => {
    const testName = data.testName;

    if (runningTest == testName) {
      console.log(`Stopping test "${testName}"`);
      io.to("rpi").emit("stop_test_rpi", testName);
      runningTest = null;

      io.to("client").emit("status_test", runningTest);
    } else {
      console.log(`Error: Test "${testName}" is not running`);
    }
  });

  socket.on("get_tests", () => {
    io.to("client").emit("status_test", runningTest);
  });

  socket.on("test_data", (data) => {
    const { testName, data: test_data } = data;
    const sender = allRPI[socket.id];

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
    io.to("client").emit("test_data", {
      testName,
      data: test_data,
      sender,
    });
  });
});

server.listen(3001, () => {
  console.log("server is running");
});
