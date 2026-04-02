import { NodeProps } from "@xyflow/react";
import { Button, Icons, Typography } from "fidesui";
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
  const hasFields = (nodeData.collection.fields?.length ?? 0) > 0;

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
        className={`${styles.button} ${getNodeHoverClass(hoverStatus)} ${nodeData.isHighlighted ? styles["button--highlighted"] : ""}`}
        type="text"
      >
        <Icons.Table size={14} style={{ flexShrink: 0 }} />
        <Typography.Text ellipsis style={{ color: "inherit" }}>
          {nodeData.label}
        </Typography.Text>
        <span className={styles.badge}>
          <Icons.Column size={10} />
          {nodeData.filteredFieldCount ?? nodeData.collection.fields?.length ?? 0}
        </span>
      </Button>
      {nodeData.isRoot && (
        <div className={styles["add-button-container"]}>
          <Button
            type="default"
            className={`${styles["add-button"]} ${hoverStatus === DatasetNodeHoverStatus.ACTIVE_HOVER ? styles["add-button--visible"] : ""}`}
            icon={<Icons.Add size={16} />}
            onClick={(e) => {
              e.stopPropagation();
              actions.addField(nodeData.collection.name);
            }}
            size="small"
            aria-label="Add field"
          />
        </div>
      )}
      {hasFields && (
        <DatasetNodeHandle
          type="source"
          inactive={hoverStatus === DatasetNodeHoverStatus.INACTIVE}
        />
      )}
    </div>
  );
};

export default DatasetCollectionNode;
