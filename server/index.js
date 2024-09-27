import express from "express";
const app = express();

import { createServer } from "http";
import cors from "cors";
app.use(cors());

import { Server } from "socket.io";

const allRPI = {};
const allData = {}; // To store all test data
const runningTests = [];

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
});

io.on("connection", (socket) => {
    socket.on("join_rpi", (data) => {
        const id = socket.id;
        const env = data.env;
        socket.join("rpi");
        allRPI[id] = env;
        console.log(`RPI ${socket.id} has joined. ENV: ${env}`);

        io.to("client").emit("status_rpis", allRPI);
    });

    socket.on("join_client", () => {
        socket.join("client");
        console.log(`Client ${socket.id} has joined`);

        // Send the current allData to the client
        io.to("client").emit("status_rpis", allRPI);
        io.to("client").emit("status_tests", runningTests);
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
        runningTests.push(testName);
        socket.to("rpi").emit("start_test", testName);
    });

    socket.on("stop_test_server", (data) => {
        const testName = data.testName;
        console.log(`Stopping test "${testName}"`);
        io.to("rpi").emit("stop_test_rpi", testName);

        const idx = runningTests.indexOf(testName);
        if (idx > -1) {
            runningTests.splice(idx, 1);
        }

        io.to("client").emit("status_tests", runningTests);
    });

    socket.on("get_tests", () => {
        io.to("client").emit("status_tests", runningTests);
    });

    socket.on("test_data", (data) => {
        const { testName, data: test_data } = data;
        const sender = allRPI[socket.id];

        if (allData[testName]) {
            if (!allData[testName]["info"]["senders"].includes(sender)) {
                allData[testName]["info"]["senders"].push(sender);
            }

            if (!allData[testName]["data"][sender]) {
                allData[testName]["data"][sender] = [];
            }
            allData[testName]["data"][sender].push(test_data);

            // Emit the updated allData to the client
            io.to("client").emit("all_data", allData);
        }
    });
});

server.listen(3001, () => {
    console.log("server is running");
});
