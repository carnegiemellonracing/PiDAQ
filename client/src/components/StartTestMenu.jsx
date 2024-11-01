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
          if (e.target.value.length > 30) {
            const sliced = e.target.value.slice(0, 30);
            return setTestName(sliced);
          }
          setTestName(e.target.value);
        }}
      />
      <button
        className="btn"
        onClick={() => {
          console.log("Starting test");
          const sliced = testName.slice(0, 30);
          emit("start_test", { testName: sliced });
          emit("get_tests");
        }}
      >
        Start Test
      </button>
    </div>
  );
}
