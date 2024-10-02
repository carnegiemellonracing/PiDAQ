export default function StopTestBtn({ testName, onClick }) {
  return (
    <button
      className="btn delete-button"
      id={`stop${testName}`}
      onClick={(e) => {
        let confirm = e.target.getAttribute("data-confirm");
        console.log();
        if (confirm === "false") {
          e.target.setAttribute("data-confirm", "true");
          e.target.innerHTML = "Confirm?";
          e.target.style.backgroundColor = "#FB618D";
        } else {
          onClick();
        }
      }}
      data-confirm={"false"}
      aria-label={`Delete ${testName}`}
    >
      Stop Test
    </button>
  );
}
