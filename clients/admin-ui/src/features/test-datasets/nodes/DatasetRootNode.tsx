import { NodeProps } from "@xyflow/react";
import { Button, Typography } from "fidesui";
import { useContext } from "react";

import DatasetEditorActionsContext from "../context/DatasetEditorActionsContext";
import {
  DatasetNodeHoverStatus,
  DatasetTreeHoverContext,
} from "../context/DatasetTreeHoverContext";
import { DATASET_ROOT_ID } from "../useDatasetGraph";
import styles from "./DatasetNode.module.scss";
import DatasetNodeHandle from "./DatasetNodeHandle";

const DatasetRootNode = ({ data, id }: NodeProps) => {
  const nodeData = data as { label: string };
  const { onMouseEnter, onMouseLeave, getNodeHoverStatus } = useContext(
    DatasetTreeHoverContext,
  );
  const actions = useContext(DatasetEditorActionsContext);
  const hoverStatus = getNodeHoverStatus(id);

  const getHoverClass = () => {
    switch (hoverStatus) {
      case DatasetNodeHoverStatus.ACTIVE_HOVER:
        return styles["button--hover"];
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
      <Button
        className={`${styles.button} ${styles["button--root"]} ${getHoverClass()}`}
        type="text"
        disabled={id === DATASET_ROOT_ID}
      >
        <Typography.Text ellipsis style={{ color: "inherit" }}>
          {nodeData.label}
        </Typography.Text>
      </Button>
      <button
        type="button"
        className={styles["add-button"]}
        onClick={(e) => {
          e.stopPropagation();
          actions.addCollection();
        }}
        title="Add collection"
      >
        +
      </button>
      <DatasetNodeHandle
        type="source"
        inactive={hoverStatus === DatasetNodeHoverStatus.INACTIVE}
      />
    </div>
  );
};

export default DatasetRootNode;
