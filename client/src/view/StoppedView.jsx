import StopTestBtn from "../components/StopTestBtn";
import PIsList from "../components/PIsList";
import TestsList from "../components/TestsList";
import TestDisplay from "../components/TestDisplay";

export default function StoppedView({
  allData,
  allRPI,
  room,
  emit,
  onRequestStopTest,
  setTestName,
  testName,
  currentTest,
}) {
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
            console.log("Starting test");
            emit("start_test", { testName });
            emit("get_tests");
          }}
        >
          Start Test
        </button>
      </div>

      <div className="info-section">
        <TestsList onStopTest={onRequestStopTest} currentTest={currentTest} />

        <PIsList allRPI={allRPI} />

        {room ? <h2>Room Code: {room}</h2> : <h2>Not in a Room</h2>}

        {Object.keys(allData).length !== 0 &&
          Object.keys(allData)
            .toReversed()
            .map((testKey) => (
              <TestDisplay
                key={testKey}
                data={allData[testKey]}
                testKey={testKey}
              />
            ))}
      </div>
    </div>
  );
}
