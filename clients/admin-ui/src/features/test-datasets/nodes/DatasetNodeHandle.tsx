import { Handle, HandleType, Position } from "@xyflow/react";
import classNames from "classnames";

import styles from "./DatasetNode.module.scss";

interface DatasetNodeHandleProps {
  type: HandleType;
  inactive?: boolean;
}

const DatasetNodeHandle = ({
  type,
  inactive = false,
}: DatasetNodeHandleProps) => (
  <Handle
    type={type}
    position={type === "source" ? Position.Right : Position.Left}
    className={classNames(
      styles.handle,
      inactive && styles["handle--inactive"],
      "transition-colors duration-300 ease-in",
    )}
  />
);

export default DatasetNodeHandle;
