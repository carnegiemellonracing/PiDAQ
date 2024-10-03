import { useCallback, useMemo, useState } from "react";

export default function DataTable({ data }) {
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

  console.log(data.length);

  return (
    <>
      <table className="data-table">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Linpot</th>
            <th>Ride Height</th>
            <th>Average Temp</th>
          </tr>
        </thead>
        <tbody>
          {data.map((entry, idx) => (
            <tr key={idx}>
              <td>{timestampFormatter(entry.timestamp)}</td>
              <td>{entry.linpot}cm</td>
              <td>{entry.ride_height}cm</td>
              <td>{entry.average_temp?.toFixed(1)}ºC</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
