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
    const [testData, setTestData] = useState({});
    const [allData, setAllData] = useState({}); // list of tests
    const [showGraph, setShowGraph] = useState({}); // To track graph visibility for each test

    useEffect(() => {
        socket.on("connect", () => {
            socket.emit("join_client", {});
            setRoom("client");

            socket.emit("get_rpis", {});
        });

        socket.on("status_rpis", (data) => {
            setAllRPI(data);
        });

        socket.on("test_data", (data) => {
            setTestData(data);

            const { sender, testName, data: test_data } = data;

            let key = `${testName}---${sender}`;

            const tempData = { ...allData };

            if (!tempData.hasOwnProperty(key)) {
                tempData[key] = [];
            }
            if (!tempData[key].includes(test_data)) {
                tempData[key].push(test_data);
            }
            setAllData({ ...tempData });
        });
    }, [socket, allData, allRPI]);

    const toggleGraph = (key) => {
        setShowGraph((prev) => ({ ...prev, [key]: !prev[key] }));
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

                {Object.keys(testData).length !== 0 && (
                    <>
                        <h2>
                            Newest Data: {testData.testName} ({testData.data[0]}
                            , {testData.data[1]})
                        </h2>
                        <h3>Sender: {testData.sender}</h3>
                    </>
                )}

                {Object.keys(allData).length !== 0 &&
                    Object.keys(allData).map((key, idx) => (
                        <div className="test-container" key={idx}>
                            <h3>{key}</h3>
                            {key in allRPI && <h3>Sender: {allRPI[key]}</h3>}
                            <button
                                className="btn toggle-graph-btn"
                                onClick={() => toggleGraph(key)}
                            >
                                {showGraph[key] ? "Show Table" : "Show Graph"}
                            </button>

                            {showGraph[key] ? (
                                <DataGraph data={allData[key]} />
                            ) : (
                                <DataTable data={allData[key]} />
                            )}
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
                    {data.map((data, idx) => (
                        <tr key={idx}>
                            <td>{data[0]}</td>
                            <td>{data[1]}</td>
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
