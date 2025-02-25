import { createIcon } from "@chakra-ui/icons";
import React from "react";

export default createIcon({
  displayName: "GreenCheckCircleIcon",
  viewBox: "0 0 16 16",
  defaultProps: {
    width: "16px",
    height: "16px",
  },
  path: (
    <path
      fill="#5A9A68"
      d="M7.00065 13.6663C3.31865 13.6663 0.333984 10.6817 0.333984 6.99967C0.333984 3.31767 3.31865 0.333008 7.00065 0.333008C10.6827 0.333008 13.6673 3.31767 13.6673 6.99967C13.6673 10.6817 10.6827 13.6663 7.00065 13.6663ZM6.33598 9.66634L11.0493 4.95234L10.1067 4.00967L6.33598 7.78101L4.44998 5.89501L3.50732 6.83767L6.33598 9.66634Z"
    />
  ),
});
