import { useCallback, useMemo, useRef, useState, useEffect } from "react";
import DataGraph from "./DataGraph";
import TireTempFrameDisplay from "./TireTempFrameDisplay";

export default function Graphs({ data, filterRecent, showImage, testName }) {
  const keys = Object.keys(data);
  const vizes = useMemo(
    () =>
      keys
        .map((key) => {
          let type = "unknown";
          if (typeof data[key][0][1] == "number") {
            type = "graph";
          } else if (
            data[key][0][1].constructor == Array &&
            data[key][0][1]?.length == 768 &&
            typeof data[key][0][1][0] == "number"
          ) {
            type = "image";
          }

          return { name: key, type };
        })
        .reduce(
          (acc, viz) => {
            if (viz.type == "graph") {
              acc.graph.push(viz.name);
            }
            if (viz.type == "image") {
              acc.image.push(viz.name);
            }
            return acc;
          },
          {
            graph: [],
            image: [],
          },
        ),
    [keys],
  );

  // Create three data graphs for each sender
  // const firstEntry = useMemo(() => data[0], [data]);
  // const firstTime = useMemo(() => firstEntry["timestamp"], [firstEntry]);
  // const lastEntry = data[data.length - 1];
  // const lastTime = useMemo(() => lastEntry["timestamp"], [lastEntry]);

  // const dateCache = useRef({});
  // const cachedDateToMillis = useCallback(
  //   (date) => {
  //     if (dateCache.current[date]) {
  //       return dateCache.current[date];
  //     }

  //     const millis = new Date(date).getTime();
  //     dateCache.current[date] = millis;
  //     return millis;
  //   },
  //   [dateCache],
  // );

  // const firstTimeMillis = useMemo(
  //   () => cachedDateToMillis(firstTime),
  //   [firstTime, cachedDateToMillis],
  // );

  // const lastTimeMillis = useMemo(
  //   () => cachedDateToMillis(lastTime),
  //   [lastTime, cachedDateToMillis],
  // );

  // const timestampFormatter = useCallback(
  //   (timestamp) => {
  //     const millis = cachedDateToMillis(timestamp);
  //     const diff = millis - firstTimeMillis;
  //     const seconds = diff / 1000;
  //     return seconds.toFixed(2);
  //   },
  //   [cachedDateToMillis, firstTimeMillis],
  // );

  // const filteredData = useMemo(() => {
  //   if (filterRecent) {
  //     return data.filter((entry) => {
  //       const millis = cachedDateToMillis(entry.timestamp);
  //       const diff = lastTimeMillis - millis;
  //       const seconds = diff / 1000;
  //       return seconds <= 10;
  //     });
  //   }

  //   return data;
  // }, [data, filterRecent, cachedDateToMillis, lastTimeMillis]);

  return (
    <div className="graph-container">
      <h3>Graphs</h3>
      <div className="graph-box">
        {vizes.graph.map((viz) => (
          <div key={viz} className="graph">
            <h4>{viz}</h4>
            <DataGraph name={viz} data={data[viz]} />
          </div>
        ))}
      </div>

      {showImage &&
        vizes.image.map((viz) => (
          <div key={viz} className="temp-canvas">
            <h4>Temperature</h4>
            <TireTempFrameDisplay lastEntry={data[viz].at(-1)[1]} />
          </div>
        ))}
    </div>
  );
}
