import { useState } from "react";
import Graphs from "../components/Graphs";
import StopTestBtn from "../components/StopTestBtn";

export default function RunningTestView({
  currentTest,
  currentTestData,
  allData,
  allRPI,
  room,
  emit,
  onRequestStopTest,
}) {
  const [viewTires, setViewTires] = useState(false);

  return (
    <div className="test-container">
      <div>
        <h3>Test Name: {currentTest}</h3>
        <StopTestBtn
          testName={currentTest}
          onClick={() => onRequestStopTest(currentTest)}
        />
        <button
          className="btn"
          onClick={() => {
            setViewTires((prev) => !prev);
          }}
        >
          {viewTires ? "Hide Tires" : "View Tires"}
        </button>
      </div>
      <h4>
        Start Time: {new Date(currentTestData.info.time).toLocaleString()}
      </h4>
      <h4>Senders: {currentTestData.info.senders.join(", ")}</h4>

      <div className="running-senders-container">
        {currentTestData.info.senders.map((senderKey) => {
          const piConnected = Object.values(allRPI).includes(senderKey);
          return (
            <div
              className={`sender-box ${!piConnected ? "sender-disconnected" : ""}`}
              key={senderKey}
            >
              <h4>Sender: {senderKey}</h4>
              <Graphs
                data={currentTestData.data[senderKey]}
                filterRecent
                showImage={viewTires}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}
