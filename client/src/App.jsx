import "./App.css";
import { useState } from "react";

import StopTestBtn from "./components/StopTestBtn";
import { useSocket } from "./hooks/useSocket";
import PIsList from "./components/PIsList";
import TestsList from "./components/TestsList";
import TestDisplay from "./components/TestDisplay";
import StoppedView from "./view/StoppedView";
import RunningTestView from "./view/RunningTestView";

function App() {
    const [testName, setTestName] = useState("");
    const { room, allRPI, currentTest, allData, emit } = useSocket();
    const onRequestStopTest = (testName) => {
        emit("stop_test_server", {
            testName: testName,
        });
    };

    const currentTestData = allData[currentTest];
    return !currentTest ? (
        <StoppedView
            allData={allData}
            allRPI={allRPI}
            room={room}
            emit={emit}
            onRequestStopTest={onRequestStopTest}
            setTestName={setTestName}
            testName={testName}
            currentTest={currentTest}
        />
    ) : (
        <RunningTestView
            currentTest={currentTest}
            currentTestData={currentTestData}
            allData={allData}
            allRPI={allRPI}
            room={room}
            emit={emit}
            onRequestStopTest={onRequestStopTest}
        />
    );
}

export default App;
