import StopTestBtn from "./StopTestBtn";

export default function TestsList({ currentTest, onStopTest }) {
  return currentTest ? (
    <>
      <h2>Currently running one test</h2>
      <div>
        <p>{currentTest}</p>
        <StopTestBtn
          onClick={() => onStopTest(currentTest)}
          testName={currentTest}
        />
      </div>
    </>
  ) : (
    <h2>No Tests Running</h2>
  );
}
