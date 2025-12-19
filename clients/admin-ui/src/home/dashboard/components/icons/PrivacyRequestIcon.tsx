import { createIcon } from "fidesui";
import * as React from "react";

/**
 * Custom privacy request icon component
 * Two overlapping documents/checkmarks representing privacy requests
 */
export const PrivacyRequestIcon = createIcon({
  displayName: "PrivacyRequestIcon",
  viewBox: "0 0 26 20",
  path: (
    <path
      d="M4.4772 17.1419L10.9772 10.0733V14.3212L5.7564 19.9987H0V17.1419H4.4772ZM20.2423 0L15.0215 5.67755V9.92286L21.5189 2.85678H26V0H20.2423ZM11.0474 0L10.9785 0.0745693L4.4785 7.14322H0V10H5.7577L10.9785 4.32245L14.9526 0H11.0474ZM20.2423 10L15.0215 15.6776L11.0461 20H14.9513L15.0202 19.9229L21.5176 12.8568H25.9987V10H20.241H20.2423Z"
      fill="currentColor"
    />
  ),
});

