import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from "recharts";

export default function DataGraph({ data, testName }) {
    return (
        <>
            <ResponsiveContainer width="100%" height={100}>
                <LineChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="independent" />
                    <YAxis />
                    <Tooltip />
                    <Line
                        type="monotone"
                        dataKey="dependent"
                        stroke="#8884d8"
                    />
                </LineChart>
            </ResponsiveContainer>
        </>
    );
}
