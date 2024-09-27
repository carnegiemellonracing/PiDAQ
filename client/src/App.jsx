import { useState, useEffect } from "react";
import "./App.css";
import io from "socket.io-client";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from "recharts";

const socket = io.connect("http://localhost:3001");

function App() {
    const [room, setRoom] = useState("");
    const [allRPI, setAllRPI] = useState({});
    const [testName, setTestName] = useState("");
    const [allData, setAllData] = useState({}); // List of tests with info and sender data
    const [showTable, setShowTable] = useState({}); // To track graph visibility for each sender in each test

    useEffect(() => {
        socket.on("connect", () => {
            socket.emit("join_client", {});
            setRoom("client");
            socket.emit("get_rpis", {});
        });

        socket.on("status_rpis", (data) => {
            setAllRPI(data);
        });

        socket.on("all_data", (data) => {
            setAllData(data);
        });
    }, []);

    const toggleGraph = (testKey, senderKey) => {
        setShowTable((prev) => ({
            ...prev,
            [testKey]: {
                ...(prev[testKey] || {}),
                [senderKey]: !(prev[testKey] || {})[senderKey],
            },
        }));
    };

    return (
        <div className="app-container">
            <div className="controls">
                <input
                    type="text"
                    className="input-field"
                    placeholder="Test Name"
                    onChange={(e) => {
                        setTestName(e.target.value);
                    }}
                />
                <button
                    className="btn"
                    onClick={() => {
                        socket.emit("start_test", { testName });
                    }}
                >
                    Start Test
                </button>
                <button
                    className="btn"
                    onClick={() => {
                        socket.emit("stop_test", { testName });
                    }}
                >
                    Stop Test
                </button>
            </div>

            <div className="info-section">
                <h1>All RPIs:</h1>
                {Object.keys(allRPI).length !== 0 && (
                    <ul className="rpi-list">
                        {Object.keys(allRPI).map((key, idx) => (
                            <li key={idx} className="rpi-item">
                                {allRPI[key]}
                            </li>
                        ))}
                    </ul>
                )}

                {room ? <h1>Room Code: {room}</h1> : <h1>Not in a Room</h1>}

                {Object.keys(allData).length !== 0 &&
                    Object.keys(allData).map((testKey, idx) => (
                        <div className="test-container" key={idx}>
                            <h3>Test Name: {allData[testKey].info.name}</h3>
                            <h4>
                                Start Time:{" "}
                                {new Date(
                                    allData[testKey].info.time
                                ).toLocaleString()}
                            </h4>
                            <h4>
                                Senders:{" "}
                                {allData[testKey].info.senders.join(", ")}
                            </h4>

                            <div className="sender-container">
                                {allData[testKey].info.senders.map(
                                    (senderKey) => (
                                        <div
                                            className="sender-box"
                                            key={senderKey}
                                        >
                                            <h4>Sender: {senderKey}</h4>
                                            <button
                                                className="btn toggle-graph-btn"
                                                onClick={() =>
                                                    toggleGraph(
                                                        testKey,
                                                        senderKey
                                                    )
                                                }
                                            >
                                                {showTable[testKey] &&
                                                showTable[testKey][senderKey]
                                                    ? "Show Graph"
                                                    : "Show Table"}
                                            </button>

                                            {showTable[testKey] &&
                                            showTable[testKey][senderKey] ? (
                                                <DataTable
                                                    data={
                                                        allData[testKey].data[
                                                            senderKey
                                                        ]
                                                    }
                                                />
                                            ) : (
                                                <DataGraph
                                                    data={
                                                        allData[testKey].data[
                                                            senderKey
                                                        ]
                                                    }
                                                />
                                            )}
                                        </div>
                                    )
                                )}
                            </div>
                        </div>
                    ))}
            </div>
        </div>
    );
}

export default App;

function DataTable({ data }) {
    return (
        <>
            <table className="data-table">
                <thead>
                    <tr>
                        <th>Independent Variable</th>
                        <th>Dependent Variable</th>
                    </tr>
                </thead>
                <tbody>
                    {data.map((entry, idx) => (
                        <tr key={idx}>
                            <td>{entry[0]}</td>
                            <td>{entry[1]}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </>
    );
}

function DataGraph({ data }) {
    return (
        <>
            <ResponsiveContainer width="100%" height={300}>
                <LineChart
                    data={data.map((d, idx) => ({
                        name: `${idx + 1}`,
                        independent: d[0],
                        dependent: d[1],
                    }))}
                >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="independent" />
                    <YAxis />
                    <Tooltip />
                    <Line
                        type="monotone"
                        dataKey="dependent"
                        stroke="#8884d8"
                    />
                </LineChart>
            </ResponsiveContainer>
        </>
    );
}
