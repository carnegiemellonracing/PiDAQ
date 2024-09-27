import { useState, useEffect } from "react";
import "./App.css";
import io from "socket.io-client";

const socket = io.connect("http://localhost:3001");

function App() {
    const [room, setRoom] = useState("");
    const [allRPI, setAllRPI] = useState({});
    const [testName, setTestName] = useState("");
    const [testData, setTestData] = useState({});
    const [allData, setAllData] = useState({}); // list of tests

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

            const { sender, testName, data: d } = data;

            let key = `${testName}---${sender}_UNKNOWN_RPI`;
            if (sender in allRPI) {
                key = `${testName}---${allRPI[sender]}`;
            }

            console.log(sender);
            console.log(allRPI);
            const tempData = { ...allData };

            if (!tempData.hasOwnProperty(key)) {
                tempData[key] = [];
            }
            if (!tempData[key].includes(d)) {
                tempData[key].push(d);
            }
            setAllData({ ...tempData });
        });
    }, [socket, allData, allRPI]);

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
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>Independent Variable</th>
                                        <th>Dependent Variable</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {allData[key].map((data, idx) => (
                                        <tr key={idx}>
                                            <td>{data[0]}</td>
                                            <td>{data[1]}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ))}
            </div>
        </div>
    );
}

export default App;
