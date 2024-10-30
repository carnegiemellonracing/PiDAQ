import DataTable from "./DataTable";
import DataGraph from "./DataGraph";
import { useState } from "react";
import Graphs from "./Graphs";

export default function TestDisplay({ data, testKey }) {
  return (
    <div className="test-container">
      <h3>Test Name: {data.info.name}</h3>
      <h4>Start Time: {new Date(data.info.time).toLocaleString()}</h4>
      <h4>Senders: {data.info.senders.join(", ")}</h4>

      <div className="sender-container">
        {data.info.senders.map((senderKey) => (
          <div className="sender-box" key={senderKey}>
            <h4>Sender: {senderKey}</h4>

            {<Graphs data={data.data[senderKey]} testName={testKey} />}
          </div>
        ))}
      </div>
    </div>
  );
}
