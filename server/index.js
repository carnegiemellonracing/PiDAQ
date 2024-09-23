import express from "express";
const app = express();

import { createServer } from "http";

import cors from "cors";
app.use(cors());

import { Server } from "socket.io";

const server = createServer(app);
const io = new Server(server, {
    cors: {
        origin: "*",
        methods: ["GET", "POST"],
    },
});

io.on("connection", (socket) => {
    console.log(`User Connected ${socket.id}`);

    socket.on("message", (data) => {
        socket.to(data.room).emit("receive_message", data);
    });

    socket.on("join_room", (data) => {
        if (data.currRoom) {
            socket.leave(data.currRoom);
            if (data.currRoom !== data.room) {
                console.log(
                    `User joined room "${data.room}" and left "${data.currRoom}"`
                );
            }
        } else {
            console.log(`User joined room "${data.room}"`);
        }
        // can add logic for if rasppi is connected, send message to client
        socket.join(data.room);
    });

    socket.on("disconnect", () => {
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
        socket.to("rasppi").emit("start_test", data.testName);
    });

    socket.on("stop_test", (data) => {
        console.log(`Stopping test "${data.testName}"`);
        socket.to("rasppi").emit("stop_test", data.testName);
    });

    socket.on("test_data", (data) => {
        socket.to("client").emit("test_data", data);
    });
});

server.listen(3001, () => {
    console.log("server is running");
});
