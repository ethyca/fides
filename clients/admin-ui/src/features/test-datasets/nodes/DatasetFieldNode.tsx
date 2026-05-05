import { NodeProps } from "@xyflow/react";
import { Button, Icons, Tag, Typography } from "fidesui";
import { useContext } from "react";

import DatasetEditorActionsContext from "../context/DatasetEditorActionsContext";
import {
  DatasetNodeHoverStatus,
  DatasetTreeHoverContext,
} from "../context/DatasetTreeHoverContext";
import { FieldNodeData } from "../useDatasetGraph";
import styles from "./DatasetNode.module.scss";
import DatasetNodeHandle from "./DatasetNodeHandle";
import { getNodeHoverClass } from "./getNodeHoverClass";

const DatasetFieldNode = ({ data, id }: NodeProps) => {
  const nodeData = data as FieldNodeData;
  const categories = nodeData.field.data_categories ?? [];
  const hasCategories = categories.length > 0;
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
        className={`${styles.button} ${getNodeHoverClass(hoverStatus)} ${!hasCategories && !nodeData.isProtected ? styles["button--no-categories"] : ""} ${nodeData.isHighlighted ? styles["button--highlighted"] : ""}`}
        type="text"
      >
        <Icons.Column size={14} style={{ flexShrink: 0 }} />
        <Typography.Text ellipsis style={{ color: "inherit" }}>
          {nodeData.label}
        </Typography.Text>
        {nodeData.isProtected && <Tag color="warning">protected</Tag>}
        {hasCategories && !nodeData.isProtected && (
          <Tag color="marble">{categories.length}</Tag>
        )}
      </Button>
      <div className={styles["add-button-container"]}>
        <Button
          type="default"
          className={`${styles["add-button"]} ${hoverStatus === DatasetNodeHoverStatus.ACTIVE_HOVER ? styles["add-button--visible"] : ""}`}
          icon={<Icons.Add size={16} />}
          onClick={(e) => {
            e.stopPropagation();
            actions.addField(nodeData.collectionName, nodeData.fieldPath);
          }}
          size="small"
          aria-label="Add nested field"
        />
      </div>
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
