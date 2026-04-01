import { NodeProps } from "@xyflow/react";
import { Button, Icons, Typography } from "fidesui";
import { useContext } from "react";

import DatasetEditorActionsContext from "../context/DatasetEditorActionsContext";
import {
  DatasetNodeHoverStatus,
  DatasetTreeHoverContext,
} from "../context/DatasetTreeHoverContext";
import { DATASET_ROOT_ID } from "../useDatasetGraph";
import styles from "./DatasetNode.module.scss";
import DatasetNodeHandle from "./DatasetNodeHandle";
import { getNodeHoverClass } from "./getNodeHoverClass";

const DatasetRootNode = ({ data, id }: NodeProps) => {
  const nodeData = data as { label: string; allowAddCollection?: boolean };
  const { onMouseEnter, onMouseLeave, getNodeHoverStatus } = useContext(
    DatasetTreeHoverContext,
  );
  const actions = useContext(DatasetEditorActionsContext);
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
        disabled={id === DATASET_ROOT_ID && !nodeData.allowAddCollection}
      >
        <Icons.Layers size={14} style={{ flexShrink: 0 }} />
        <Typography.Text ellipsis style={{ color: "inherit" }}>
          {nodeData.label}
        </Typography.Text>
      </Button>
      {nodeData.allowAddCollection && (
        <div className={styles["add-button-container"]}>
          <Button
            type="default"
            className={`${styles["add-button"]} ${hoverStatus === DatasetNodeHoverStatus.ACTIVE_HOVER ? styles["add-button--visible"] : ""}`}
            icon={<Icons.Add size={16} />}
            onClick={(e) => {
              e.stopPropagation();
              actions.addCollection();
            }}
            size="small"
            aria-label="Add collection"
          />
        </div>
      )}
      <DatasetNodeHandle
        type="source"
        inactive={hoverStatus === DatasetNodeHoverStatus.INACTIVE}
      />
    </div>
  );
};

export default DatasetRootNode;
