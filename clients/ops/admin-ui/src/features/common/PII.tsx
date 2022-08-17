import React from "react";

import { useObscuredPII } from "../privacy-requests/helpers";

const PII: React.FC<{ data: string }> = ({ data }) => (
  <>{useObscuredPII(data)}</>
);

export default PII;
