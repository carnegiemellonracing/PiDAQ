export default function PIsList({ allRPI }) {
  return Object.keys(allRPI).length !== 0 ? (
    <>
      <h2>All RPIs Connected:</h2>
      <ul className="rpi-list list">
        {Object.keys(allRPI).map((key, idx) => (
          <li key={idx} className="list-item">
            {allRPI[key]}
          </li>
        ))}
      </ul>
    </>
  ) : (
    <h2>No RPIs connected</h2>
  );
}
