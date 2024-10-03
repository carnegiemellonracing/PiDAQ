import Graphs from "../components/Graphs";
import StopTestBtn from "../components/StopTestBtn";

export default function RunningTestView({
  currentTest,
  currentTestData,
  allData,
  allRPI,
  allTests,
  room,
  emit,
  onRequestStopTest,
}) {
  console.log("currentTest", currentTest);
  console.log("currentTestData", currentTestData);
  return (
    <div className="test-container">
      <div>
        <h3>Test Name: {currentTest}</h3>
        <StopTestBtn
          testName={currentTest}
          onClick={() => onRequestStopTest(currentTest)}
        />
      </div>
      <h4>
        Start Time: {new Date(currentTestData.info.time).toLocaleString()}
      </h4>
      <h4>Senders: {currentTestData.info.senders.join(", ")}</h4>

      <div className="running-senders-container">
        {currentTestData.info.senders.map((senderKey) => (
          <div className="sender-box" key={senderKey}>
            <h4>Sender: {senderKey}</h4>
            <Graphs data={currentTestData.data[senderKey]} />
          </div>
        ))}
      </div>
    </div>
  );
}
