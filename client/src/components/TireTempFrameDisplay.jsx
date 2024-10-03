import { useEffect, useRef, useState } from "react";
import { useThrottledCallback } from "use-debounce";

export default function TireTempFrameDisplay({ lastEntry }) {
  const canvasRef = useRef(null);

  const [lastImage, setLastImage] = useState(lastEntry?.["tire_temp_frame"]);

  const onRefresh = useRef(null);

  const throttledOnRefresh = useThrottledCallback(() => {
    onRefresh.current();
  }, 500);

  useEffect(() => {
    onRefresh.current = () => {
      setLastImage(lastEntry["tire_temp_frame"]);
    };
  }, [lastEntry]);

  useEffect(() => {
    throttledOnRefresh();
  }, [lastEntry, throttledOnRefresh]);

  // Function to convert temperature to color (for example: blue for cold, red for hot)
  const tempToColor = (temp) => {
    // Define a range of temperatures for color mapping
    const minTemp = 20; // Example minimum temperature
    const maxTemp = 50; // Example maximum temperature

    // Normalize temperature between 0 and 1
    const normalizedTemp = (temp - minTemp) / (maxTemp - minTemp);

    // Map the normalized temperature to RGB (example: blue (cold) to red (hot))
    const r = Math.min(255, Math.max(0, Math.round(255 * normalizedTemp))); // Red increases with temperature
    const g = 0; // For simplicity, we keep green 0
    const b = Math.min(
      255,
      Math.max(0, Math.round(255 * (1 - normalizedTemp))),
    ); // Blue decreases with temperature

    return `rgb(${r},${g},${b})`;
  };

  useEffect(() => {
    if (!lastImage) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const width = 32;
    const height = 24;

    // Ensure the frame has the correct number of values
    if (lastImage.length !== width * height) {
      console.error("Invalid frame data");
      return;
    }

    // Set the canvas size to match the 32x24 grid
    canvas.width = width;
    canvas.height = height;

    // Draw each pixel on the canvas
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const index = y * width + x;
        const temp = lastImage[index];
        const color = tempToColor(temp);

        ctx.fillStyle = color;
        ctx.fillRect(x, y, 1, 1); // Draw a single pixel
      }
    }
  }, [lastImage]);

  return (
    <div className="tire-temp-frame-display">
      <canvas ref={canvasRef} />
    </div>
  );
}
