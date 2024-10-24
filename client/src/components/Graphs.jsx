import { useCallback, useMemo, useRef, useState, useEffect } from "react";
import DataGraph from "./DataGraph";
import TireTempFrameDisplay from "./TireTempFrameDisplay";

export default function Graphs({ data, filterRecent, showImage, testName }) {
    // Create three data graphs for each sender
    const firstEntry = useMemo(() => data[0], [data]);
    const firstTime = useMemo(() => firstEntry["timestamp"], [firstEntry]);
    const lastEntry = data[data.length - 1];
    const lastTime = useMemo(() => lastEntry["timestamp"], [lastEntry]);

    const dateCache = useRef({});
    const cachedDateToMillis = useCallback(
        (date) => {
            if (dateCache.current[date]) {
                return dateCache.current[date];
            }

            const millis = new Date(date).getTime();
            dateCache.current[date] = millis;
            return millis;
        },
        [dateCache]
    );

    const firstTimeMillis = useMemo(
        () => cachedDateToMillis(firstTime),
        [firstTime, cachedDateToMillis]
    );

    const lastTimeMillis = useMemo(
        () => cachedDateToMillis(lastTime),
        [lastTime, cachedDateToMillis]
    );

    const timestampFormatter = useCallback(
        (timestamp) => {
            const millis = cachedDateToMillis(timestamp);
            const diff = millis - firstTimeMillis;
            const seconds = diff / 1000;
            return seconds.toFixed(2);
        },
        [cachedDateToMillis, firstTimeMillis]
    );

    const filteredData = useMemo(() => {
        if (filterRecent) {
            return data.filter((entry) => {
                const millis = cachedDateToMillis(entry.timestamp);
                const diff = lastTimeMillis - millis;
                const seconds = diff / 1000;
                return seconds <= 10;
            });
        }

        return data;
    }, [data, filterRecent, cachedDateToMillis, lastTimeMillis]);

    const ride_height = filteredData
        .map((entry, idx) => ({
            name: `${idx + 1}`,
            independent: timestampFormatter(entry.timestamp),
            dependent: entry.ride_height,
        }))
        .filter((entry) => entry.dependent !== false);

    const linpot = filteredData
        .map((entry, idx) => ({
            name: `${idx + 1}`,
            independent: timestampFormatter(entry.timestamp),
            dependent: entry.linpot,
        }))
        .filter((entry) => entry.dependent !== false);

    const average_temp = filteredData
        .map((entry, idx) => ({
            name: `${idx + 1}`,
            independent: timestampFormatter(entry.timestamp),
            dependent: entry.tire_temp_frame,
        }))
        .filter((entry) => entry.dependent !== false);

    return (
        <div className="graph-container">
            <h3>Graphs</h3>
            <div className="graph-box">
                {ride_height.length > 0 && (
                    <>
                        <h4>Ride Height</h4>
                        <DataGraph data={ride_height} testName={testName} />
                    </>
                )}

                {linpot.length > 0 && (
                    <>
                        <h4>Linpot</h4>
                        <DataGraph data={linpot} testName={testName} />
                    </>
                )}

                {average_temp.length > 0 && (
                    <>
                        <h4>Average Temp</h4>
                        <DataGraph data={average_temp} testName={testName} />
                    </>
                )}
            </div>
            {showImage && (
                <div className="temp-canvas">
                    <h4>Temperature</h4>
                    <TireTempFrameDisplay lastEntry={lastEntry} />
                </div>
            )}
        </div>
    );
}
