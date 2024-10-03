import { useEffect, useState } from "react";
import io from "socket.io-client";

export function useSocket() {
  const [socket, setSocket] = useState(null);
  useEffect(() => {
    setSocket(io.connect("http://localhost:3001"));
  }, []);

  const [room, setRoom] = useState("");
  const [allRPI, setAllRPI] = useState({});
  const [currentTest, setCurrentTest] = useState(null);
  const [allData, setAllData] = useState({}); // List of tests with info and sender data

  useEffect(() => {
    if (socket) {
      socket.on("connect", () => {
        socket.emit("join_client", {});
        setRoom("client");
      });

      socket.on("status_rpis", (data) => {
        setAllRPI(data);
      });

      socket.on("status_test", (data) => {
        setCurrentTest(data);
      });

      socket.on("all_data", (data) => {
        setAllData(data);
      });
    }
  }, [socket]);

  useEffect(() => {
    const cb = (data) => {
      const { testName, data: test_data, sender } = data;

      setAllData((prevData) => {
        const updatedData = { ...prevData }; // Create a shallow copy of the previous state

        if (updatedData[testName]) {
          // If testName already exists
          if (!updatedData[testName]["info"]["senders"].includes(sender)) {
            updatedData[testName]["info"]["senders"].push(sender); // Add sender if not already present
          }
          if (!updatedData[testName]["data"][sender]) {
            updatedData[testName]["data"][sender] = []; // Initialize sender data array if it doesn't exist
          }
          updatedData[testName]["data"][sender].push(test_data); // Push test_data into the sender's data array
        } else {
          console.log("No test data found for", testName);
        }

        return updatedData; // Return the updated state
      });
    };

    if (socket) {
      socket.on("test_data", cb);
      return () => socket.off("test_data", cb);
    }
  }, [socket, allData, allRPI]);

  const emit = (...params) => {
    if (socket) {
      socket.emit(...params);
    }
  };

  return {
    room,
    allRPI,
    currentTest,
    allData,
    emit,
  };
}
