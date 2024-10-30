import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function DataGraph({ name, data }) {
  const formattedData = data.map(([timestamp, value]) => {
    return {
      independent: timestamp,
      dependent: name == "tire_temp_avg" ? value / 100 : value,
    };
  });

  return (
    <>
      <ResponsiveContainer width="100%" height={100}>
        <LineChart data={formattedData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="independent" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="dependent" stroke="#8884d8" />
        </LineChart>
      </ResponsiveContainer>
    </>
  );
}
