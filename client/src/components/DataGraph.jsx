// Importing necessary components from the 'recharts' library for creating a responsive (meaning it can adjust size and layout to fit the screen) line chart.
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

// Defining the DataGraph component, which takes 'name' and 'data' as props.
export default function DataGraph({ name, data }) {
  // Formatting the input data to match the structure required by the LineChart (which is a component from the recharts library).
  // we needa do this bc LineChart (from a library) expects the data to be an array of objects, where each object reps a single data point with specific keys independent (which is the timestamp, x) and dependent (which is the value, y).
  const formattedData = data.map(([timestamp, value]) => {
    return {
      independent: timestamp, // 'independent' represents the x-axis value (timestamp).
      dependent: name == "tire_temp_avg" ? value / 100 : value, // 'dependent' represents the y-axis value, but if the name is "tire_temp_avg", then we needa scale the value by dividing by 100.
    };
  });

  return (
    <>
      {/* Wrapping the LineChart in a ResponsiveContainer to ensure it adjusts to the parent container's size. */}
      <ResponsiveContainer width="100%" height={100}>
        {/* Creating a LineChart with the formatted data (the array of objects). */}
        <LineChart data={formattedData}>
          {/* Adding a grid with dashed lines for better readability. */}
          <CartesianGrid strokeDasharray="3 3" />
          {/* Defining the x-axis, which uses the 'independent' key from the data. */}
          <XAxis dataKey="independent" />
          {/* Defining the y-axis, which automatically scales based on the data. (designed like so by the library)*/}
          <YAxis />
          {/* Adding a tooltip to display data values on hover. */}
          <Tooltip />
          {/* Adding a line to the chart, which represents the 'dependent' values. */}
          <Line type="monotone" dataKey="dependent" stroke="#8884d8" />
        </LineChart>
      </ResponsiveContainer>
    </>
  );
}
