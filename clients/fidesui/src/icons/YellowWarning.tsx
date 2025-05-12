import { createIcon } from "@chakra-ui/icons";
import React from "react";

export default createIcon({
  displayName: "YellowWarningIcon",
  viewBox: "0 0 16 16",
  defaultProps: {
    width: "16px",
    height: "16px",
  },
  path: (
    <>
      <circle cx="8" cy="8" r="7" fill="#e59d47" />
      <path
        d="M8 4.5C8.41421 4.5 8.75 4.83579 8.75 5.25V8.25C8.75 8.66421 8.41421 9 8 9C7.58579 9 7.25 8.66421 7.25 8.25V5.25C7.25 4.83579 7.58579 4.5 8 4.5Z"
        fill="#FFFFFF"
      />
      <path
        d="M8 10.5C8.41421 10.5 8.75 10.8358 8.75 11.25C8.75 11.6642 8.41421 12 8 12C7.58579 12 7.25 11.6642 7.25 11.25C7.25 10.8358 7.58579 10.5 8 10.5Z"
        fill="#FFFFFF"
      />
    </>
  ),
});
