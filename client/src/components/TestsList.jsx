import StopTestBtn from "./StopTestBtn";

export default function TestsList({ allTests, onStopTest }) {
  return allTests.length !== 0 ? (
    <>
      <h2>All Tests Running:</h2>
      <ul className="test-list list">
        {allTests.map((testName) => (
          <li key={testName} className="list-item">
            <p>{testName}</p>
            <StopTestBtn
              onClick={() => onStopTest(testName)}
              testName={testName}
            />
          </li>
        ))}
      </ul>
    </>
  ) : (
    <h2>No Tests Running</h2>
  );
}
