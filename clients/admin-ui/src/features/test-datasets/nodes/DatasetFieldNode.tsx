import { NodeProps } from "@xyflow/react";
import { Button, Typography } from "fidesui";
import { useContext } from "react";

import DatasetEditorActionsContext from "../context/DatasetEditorActionsContext";
import {
  DatasetNodeHoverStatus,
  DatasetTreeHoverContext,
} from "../context/DatasetTreeHoverContext";
import { FieldNodeData } from "../useDatasetGraph";
import styles from "./DatasetNode.module.scss";
import DatasetNodeHandle from "./DatasetNodeHandle";

const DatasetFieldNode = ({ data, id }: NodeProps) => {
  const nodeData = data as FieldNodeData;
  const categories = nodeData.field.data_categories ?? [];
  const { onMouseEnter, onMouseLeave, getNodeHoverStatus } = useContext(
    DatasetTreeHoverContext,
  );
  const actions = useContext(DatasetEditorActionsContext);
  const hoverStatus = getNodeHoverStatus(id);

  const getHoverClass = () => {
    if (nodeData.isProtected) {
      return styles["button--protected"];
    }
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
      <Button
        className={`${styles.button} ${getHoverClass()} ${(data as Record<string, unknown>).isHighlighted ? styles["button--highlighted"] : ""}`}
        type="text"
      >
        <Typography.Text ellipsis style={{ color: "inherit" }}>
          {nodeData.label}
        </Typography.Text>
        {nodeData.isProtected && (
          <span className={`${styles.badge} ${styles["badge--warning"]}`}>
            protected
          </span>
        )}
        {categories.length > 0 && !nodeData.isProtected && (
          <span className={`${styles.badge} ${styles["badge--muted"]}`}>
            {categories.length}
          </span>
        )}
      </Button>
      <button
        type="button"
        className={styles["add-button"]}
        onClick={(e) => {
          e.stopPropagation();
          actions.addField(nodeData.collectionName, nodeData.fieldPath);
        }}
        title="Add nested field"
        aria-label="Add nested field"
      >
        +
      </button>
      {nodeData.hasChildren && (
        <DatasetNodeHandle
          type="source"
          inactive={hoverStatus === DatasetNodeHoverStatus.INACTIVE}
        />
      )}
    </div>
  );
};

export default DatasetFieldNode;
