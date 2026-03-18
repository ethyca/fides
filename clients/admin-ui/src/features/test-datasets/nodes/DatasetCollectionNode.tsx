import { NodeProps } from "@xyflow/react";
import { Button, Typography } from "fidesui";
import { useContext } from "react";

import DatasetEditorActionsContext from "../context/DatasetEditorActionsContext";
import {
  DatasetNodeHoverStatus,
  DatasetTreeHoverContext,
} from "../context/DatasetTreeHoverContext";
import { CollectionNodeData } from "../useDatasetGraph";
import styles from "./DatasetNode.module.scss";
import DatasetNodeHandle from "./DatasetNodeHandle";
import { getNodeHoverClass } from "./getNodeHoverClass";

const DatasetCollectionNode = ({ data, id }: NodeProps) => {
  const nodeData = data as CollectionNodeData;
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
      <DatasetNodeHandle
        type="target"
        inactive={hoverStatus === DatasetNodeHoverStatus.INACTIVE}
      />
      <Button
        className={`${styles.button} ${getNodeHoverClass(hoverStatus)} ${(data as Record<string, unknown>).isHighlighted ? styles["button--highlighted"] : ""}`}
        type="text"
      >
        <Typography.Text ellipsis style={{ color: "inherit" }}>
          {nodeData.label}
        </Typography.Text>
        <span className={styles.badge}>
          {nodeData.collection.fields?.length ?? 0}
        </span>
      </Button>
      {nodeData.isRoot && (
        <button
          type="button"
          className={styles["add-button"]}
          onClick={(e) => {
            e.stopPropagation();
            actions.addField(nodeData.collection.name);
          }}
          title="Add field"
          aria-label="Add field"
        >
          +
        </button>
      )}
      <DatasetNodeHandle
        type="source"
        inactive={hoverStatus === DatasetNodeHoverStatus.INACTIVE}
      />
    </div>
  );
};

export default DatasetCollectionNode;
