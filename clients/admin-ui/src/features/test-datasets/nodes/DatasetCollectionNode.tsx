import { NodeProps } from "@xyflow/react";
import { Button, Typography } from "fidesui";
import { useContext } from "react";

import {
  DatasetNodeHoverStatus,
  DatasetTreeHoverContext,
} from "../context/DatasetTreeHoverContext";
import { CollectionNodeData } from "../useDatasetGraph";
import styles from "./DatasetNode.module.scss";
import DatasetNodeHandle from "./DatasetNodeHandle";

const DatasetCollectionNode = ({ data, id }: NodeProps) => {
  const nodeData = data as CollectionNodeData;
  const { onMouseEnter, onMouseLeave, getNodeHoverStatus } = useContext(
    DatasetTreeHoverContext,
  );
  const hoverStatus = getNodeHoverStatus(id);

  const getHoverClass = () => {
    switch (hoverStatus) {
      case DatasetNodeHoverStatus.ACTIVE_HOVER:
        return styles["button--hover"];
      case DatasetNodeHoverStatus.PARENT_OF_HOVER:
        return styles["button--parent-hover"];
      case DatasetNodeHoverStatus.INACTIVE:
        return styles["button--inactive"];
      default:
        return "";
    }
  };

  return (
    <div
      className={styles.container}
      onMouseEnter={() => onMouseEnter(id)}
      onMouseLeave={() => onMouseLeave()}
    >
      <DatasetNodeHandle
        type="target"
        inactive={hoverStatus === DatasetNodeHoverStatus.INACTIVE}
      />
      <Button className={`${styles.button} ${getHoverClass()}`} type="text">
        <Typography.Text ellipsis style={{ color: "inherit" }}>
          {nodeData.label}
        </Typography.Text>
        <span className={styles.badge}>
          {nodeData.collection.fields.length}
        </span>
      </Button>
      <DatasetNodeHandle
        type="source"
        inactive={hoverStatus === DatasetNodeHoverStatus.INACTIVE}
      />
    </div>
  );
};

export default DatasetCollectionNode;
