import { createIcon } from "fidesui";
import * as React from "react";

/**
 * Custom consent icon component
 * Two overlapping arrows/chevrons representing consent exchange
 */
export const ConsentIcon = createIcon({
  displayName: "ConsentIcon",
  viewBox: "0 0 26 20",
  path: (
    <path
      d="M22.147 12H25.9987L18.8712 20H15.0168L22.147 12ZM25.9987 8L18.8686 0H15.0207V0.00257152L22.1483 8H26H25.9987ZM10.9754 0.00514304L10.9819 0H7.13014L0 8H3.85171L10.9754 0.00514304ZM0 12L7.12754 20H10.9819L3.85171 12H0ZM4.42888 8.57216V11.4291H10.9754V8.57216H4.42888ZM15.0207 8.57216V11.4291H21.5698V8.57216H15.0207Z"
      fill="currentColor"
    />
  ),
});

