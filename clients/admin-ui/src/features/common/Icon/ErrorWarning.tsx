import { createIcon } from "@fidesui/react";

export default createIcon({
  displayName: "ErrorWarningIcon",
  viewBox: "0 0 20 20",
  defaultProps: {
    width: "20px",
    height: "20px",
  },
  path: (
    <path
      d="M10.0003 18.3332C5.39783 18.3332 1.66699 14.6023 1.66699 9.99984C1.66699 5.39734 5.39783 1.6665 10.0003 1.6665C14.6028 1.6665 18.3337 5.39734 18.3337 9.99984C18.3337 14.6023 14.6028 18.3332 10.0003 18.3332ZM9.16699 12.4998V14.1665H10.8337V12.4998H9.16699ZM9.16699 5.83317V10.8332H10.8337V5.83317H9.16699Z"
      fill="#E53E3E"
    />
  ),
});
