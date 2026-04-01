import { NodeProps } from "@xyflow/react";
import { Button, Icons, Typography } from "fidesui";
import { useContext } from "react";

import {
  DatasetNodeHoverStatus,
  DatasetTreeHoverContext,
} from "../context/DatasetTreeHoverContext";
import { DATASET_ROOT_ID } from "../useDatasetGraph";
import styles from "./DatasetNode.module.scss";
import DatasetNodeHandle from "./DatasetNodeHandle";
import { getNodeHoverClass } from "./getNodeHoverClass";

const DatasetRootNode = ({ data, id }: NodeProps) => {
  const nodeData = data as { label: string };
  const { onMouseEnter, onMouseLeave, getNodeHoverStatus } = useContext(
    DatasetTreeHoverContext,
  );
  const hoverStatus = getNodeHoverStatus(id);

  return (
    <div
      className={styles.container}
      onMouseEnter={() => onMouseEnter(id)}
      onMouseLeave={() => onMouseLeave()}
    >
      <Button
        className={`${styles.button} ${styles["button--root"]} ${getNodeHoverClass(hoverStatus)}`}
        type="text"
        disabled={id === DATASET_ROOT_ID}
      >
        <Icons.Layers size={14} />
        <Typography.Text ellipsis style={{ color: "inherit" }}>
          {nodeData.label}
        </Typography.Text>
      </Button>
      <DatasetNodeHandle
        type="source"
        inactive={hoverStatus === DatasetNodeHoverStatus.INACTIVE}
      />
    </div>
  );
};

export default DatasetRootNode;
