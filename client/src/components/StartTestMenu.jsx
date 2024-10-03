import { useState } from "react";

export default function StartTestMenu({ emit }) {
  const [testName, setTestName] = useState("");

  return (
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
  );
}
