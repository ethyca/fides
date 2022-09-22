import { useObscuredPII } from "privacy-requests/helpers";
import React from "react";

const PII: React.FC<{ data: string }> = ({ data }) => (
  <>{useObscuredPII(data)}</>
);

export default PII;
