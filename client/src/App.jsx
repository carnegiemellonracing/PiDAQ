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
  const { room, allRPI, allTests, allData, emit } = useSocket();
  const onRequestStopTest = (testName) => {
    emit("stop_test_server", {
      testName,
    });
  };

  const currentTest = allTests[0];
  const currentTestData = allData[currentTest];

  console.log("allTests", allTests);

  return allTests.length == 0 || !currentTestData ? (
    <StoppedView
      allData={allData}
      allRPI={allRPI}
      allTests={allTests}
      room={room}
      emit={emit}
      onRequestStopTest={onRequestStopTest}
      setTestName={setTestName}
      testName={testName}
    />
  ) : (
    <RunningTestView
      currentTest={currentTest}
      currentTestData={currentTestData}
      allData={allData}
      allRPI={allRPI}
      allTests={allTests}
      room={room}
      emit={emit}
      onRequestStopTest={onRequestStopTest}
    />
  );
}

export default App;
