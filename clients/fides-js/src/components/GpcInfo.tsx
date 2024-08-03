import { h } from "preact";

import WarningIcon from "./WarningIcon";

const GpcInfo = ({
  title,
  description,
}: {
  title: string;
  description: string;
}) => (
  <div className="fides-gpc-banner">
    <div className="fides-gpc-warning">
      <WarningIcon />
    </div>
    <div>
      <p className="fides-gpc-header">{title}</p>
      <p>{description}</p>
    </div>
  </div>
);

export default GpcInfo;
