import { createIcon } from "@chakra-ui/icons";
import React from "react";

export default createIcon({
  displayName: "ErrorWarningIcon",
  viewBox: "0 0 16 16",
  defaultProps: {
    width: "16px",
    height: "16px",
  },
  path: (
    <path
      d="M8.00001 14.6668C4.31801 14.6668 1.33334 11.6822 1.33334 8.00016C1.33334 4.31816 4.31801 1.3335 8.00001 1.3335C11.682 1.3335 14.6667 4.31816 14.6667 8.00016C14.6667 11.6822 11.682 14.6668 8.00001 14.6668ZM7.33334 10.0002V11.3335H8.66668V10.0002H7.33334ZM7.33334 4.66683V8.66683H8.66668V4.66683H7.33334Z"
      fill="#E53E3E"
    />
  ),
});
