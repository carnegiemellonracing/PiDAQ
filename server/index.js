import express from "express";
const app = express();

import { createServer } from "http";

import cors from "cors";
app.use(cors());

import { Server } from "socket.io";

const allRPI = {};

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

    socket.on("join_client", (data) => {
        socket.join("client");
        console.log(`Client ${socket.id} has joined`);
    });

    socket.on("disconnect", () => {
        if (socket.id in allRPI) {
            delete allRPI[socket.id];
            io.to("client").emit("status_rpis", allRPI);
        }
        console.log(`User ${socket.id} disconnected`);
    });

    socket.on("disconnecting", () => {
        // add logic for if rasppi is disconnecting, send message to client
        console.log(`User ${socket.id} disconnecting`);
    });

    socket.on("connect_error", () => {
        // add logic for if rasppi is having trouble connecting, send message to client
        console.log(`User ${socket.id} had connection error`);
    });

    socket.on("start_test", (data) => {
        console.log(`Starting test "${data.testName}"`);
        socket.to("rpi").emit("start_test", data.testName);
    });

    socket.on("stop_test", (data) => {
        console.log(`Stopping test "${data.testName}"`);
        socket.to("rpi").emit("stop_test", data.testName);
    });

    socket.on("test_data", (data) => {
        socket.to("client").emit("test_data", { ...data, sender: socket.id });
    });

    socket.on("get_rpis", (data) => {
        io.to("client").emit("status_rpis", allRPI);
    });
});

server.listen(3001, () => {
    console.log("server is running");
});
