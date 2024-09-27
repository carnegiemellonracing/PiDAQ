import express from "express";
const app = express();

import { createServer } from "http";
import cors from "cors";
app.use(cors());

import { Server } from "socket.io";

const allRPI = {};
const allData = {}; // To store all test data

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
        console.log(allRPI);
        console.log(`RPI ${socket.id} has joined. ENV: ${env}`);

        io.to("client").emit("status_rpis", allRPI);
    });

    socket.on("join_client", () => {
        socket.join("client");
        console.log(`Client ${socket.id} has joined`);

        // Send the current allData to the client
        io.to("client").emit("status_rpis", allRPI);
        io.to("client").emit("all_data", allData);
    });

    socket.on("disconnect", () => {
        if (socket.id in allRPI) {
            delete allRPI[socket.id];
            io.to("client").emit("status_rpis", allRPI);
        }
        console.log(`User ${socket.id} disconnected`);
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
        socket.to("rpi").emit("start_test", testName);
    });

    socket.on("stop_test", (data) => {
        console.log(`Stopping test "${data.testName}"`);
        socket.to("rpi").emit("stop_test", data.testName);
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
