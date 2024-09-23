import { useState, useEffect } from "react";
import "./App.css";

import io from "socket.io-client";

const socket = io.connect("http://localhost:3001");

function App() {
    const [room, setRoom] = useState("");
    const [roomInput, setRoomInput] = useState(0);
    const [testName, setTestName] = useState("");
    const [testData, setTestData] = useState({});

    const [allData, setAllData] = useState({}); // list of tests

    const [message, setMessage] = useState("");
    const [messageReceived, setMessageReceived] = useState("");

    useEffect(() => {
        socket.on("connect", () => {
            socket.emit("join_room", { room: "client", currRoom: room });
            setRoom("client");
        });
        socket.on("receive_message", (data) => {
            setMessageReceived(data.message);
        });

        socket.on("test_data", (data) => {
            setTestData(data);

            const { sender, testName, data: d } = data;

            const key = `${testName}-${sender}`;
            const tempData = { ...allData };

            if (!tempData.hasOwnProperty(key)) {
                tempData[key] = [];
            }
            if (!tempData[key].includes(d)) {
                tempData[key].push(d);
            }
            setAllData({ ...tempData });
        });
    }, [socket, allData]);

    return (
        <>
            <input
                type="text"
                placeholder="Test Name"
                onChange={(e) => {
                    setTestName(e.target.value);
                }}
            />
            <button
                onClick={() => {
                    socket.emit("start_test", { testName });
                }}
            >
                Start Test
            </button>

            <button
                onClick={() => {
                    socket.emit("stop_test", { testName });
                }}
            >
                Stop Test
            </button>
            <br />
            <input
                type="text"
                placeholder="Room Code"
                value=""
                onChange={(event) => {
                    setRoomInput(event.target.value);
                }}
            />
            <button
                onClick={() => {
                    socket.emit("join_room", {
                        room: roomInput,
                        currRoom: room,
                    });
                    setRoom(roomInput);
                }}
            >
                Join Room
            </button>
            <br />
            <input
                type="text"
                placeholder="Message"
                onChange={(event) => setMessage(event.target.value)}
            />
            <button
                onClick={() => {
                    console.log(allData);
                    socket.emit("message", {
                        message,
                        room,
                    });
                }}
            >
                Send Message
            </button>
            {room ? <h1>Room Code: {room}</h1> : <h1>Not in a Room</h1>}

            {messageReceived && (
                <>
                    <h1>Message Received:</h1>
                    <p>{messageReceived}</p>
                </>
            )}

            {Object.keys(testData).length !== 0 && (
                <>
                    <h2>
                        Newest Data: {testData.testName} ({testData.data[0]},{" "}
                        {testData.data[1]})
                    </h2>
                    <h3>Sender: {testData.sender}</h3>
                </>
            )}
            {Object.keys(allData).length !== 0 &&
                Object.keys(allData).map((key, idx) => {
                    const datapoints = allData[key].map((data, idx) => {
                        return (
                            <li
                                key={(data, idx)}
                            >{`(${data[0]}, ${data[1]})`}</li>
                        );
                    });
                    return (
                        <div className="test-container" key={idx}>
                            <h3>{key}</h3>
                            <ul>{datapoints}</ul>
                        </div>
                    );
                })}
        </>
    );
}

export default App;
