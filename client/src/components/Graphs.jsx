import { useCallback, useMemo, useState } from "react";
import DataGraph from "./DataGraph";

export default function Graphs({ data }) {
  // Create three data graphs for each sender
  const firstEntry = useMemo(() => data[0], [data]);
  const firstTime = useMemo(() => firstEntry["timestamp"], [firstEntry]);

  const [dateCache, setDateCache] = useState({});
  const cachedDateToMillis = useCallback(
    (date) => {
      if (dateCache[date]) {
        return dateCache[date];
      }

      const millis = new Date(date).getTime();
      setDateCache((prev) => ({
        ...prev,
        [date]: millis,
      }));
      return millis;
    },
    [dateCache],
  );

  const firstTimeMillis = useMemo(
    () => cachedDateToMillis(firstTime),
    [firstTime, cachedDateToMillis],
  );
  cachedDateToMillis;

  const timestampFormatter = useCallback(
    (timestamp) => {
      const millis = cachedDateToMillis(timestamp);
      const diff = millis - firstTimeMillis;
      const seconds = diff / 1000;
      return seconds.toFixed(2);
    },
    [cachedDateToMillis, firstTimeMillis],
  );

  const ride_height = data.map((entry, idx) => ({
    name: `${idx + 1}`,
    independent: timestampFormatter(entry.timestamp),
    dependent: entry.ride_height,
  }));

  const linpot = data.map((entry, idx) => ({
    name: `${idx + 1}`,
    independent: timestampFormatter(entry.timestamp),
    dependent: entry.linpot,
  }));

  const average_temp = data.map((entry, idx) => ({
    name: `${idx + 1}`,
    independent: timestampFormatter(entry.timestamp),
    dependent: entry.average_temp,
  }));

  return (
    <div className="graph-container">
      <h3>Graphs</h3>
      <div className="graph-box">
        <h4>Ride Height</h4>
        <DataGraph data={ride_height} />

        <h4>Linpot</h4>
        <DataGraph data={linpot} />

        <h4>Average Temp</h4>
        <DataGraph data={average_temp} />
      </div>
    </div>
  );
}
