import { Handle, Node, NodeProps, Position } from "@xyflow/react";
import { AntButton, AntTypography, Icons, SmallAddIcon } from "fidesui";
import { useCallback, useContext } from "react";

import {
  TaxonomyTreeHoverContext,
  TreeNodeHoverStatus,
} from "../context/TaxonomyTreeHoverContext";
import { TaxonomyEntity } from "../types";
import styles from "./TaxonomyTreeNode.module.scss";
import TaxonomyTreeNodeHandle from "./TaxonomyTreeNodeHandle";

export type TaxonomyTreeNodeType = Node<
  {
    label: string;
    taxonomyItem?: TaxonomyEntity;
    onTaxonomyItemClick: (taxonomyItem: TaxonomyEntity) => void | null;
    onAddButtonClick: (taxonomyItem: TaxonomyEntity | undefined) => void;
  },
  "taxonomyTreeNode"
>;

const TaxonomyTreeNode = ({ data }: NodeProps<TaxonomyTreeNodeType>) => {
  const { onMouseEnter, onMouseLeave, getNodeHoverStatus } = useContext(
    TaxonomyTreeHoverContext,
  );
  const { taxonomyItem, onAddButtonClick, onTaxonomyItemClick, label } = data;

  const nodeHoverStatus = getNodeHoverStatus(taxonomyItem?.fides_key!);
  const getNodeHoverStatusClass = useCallback(() => {
    switch (nodeHoverStatus) {
      case TreeNodeHoverStatus.ACTIVE_HOVER:
        return styles["button-hover"];
      case TreeNodeHoverStatus.PATH_HOVER:
        return styles["button-path-hover"];
      case TreeNodeHoverStatus.INACTIVE:
        return styles["button-inactive"];
      case TreeNodeHoverStatus.DEFAULT:
        return styles["button-default"];
      default:
        return "";
    }
  }, [nodeHoverStatus]);

  return (
    <div
      className="group relative"
      onMouseEnter={() => onMouseEnter(taxonomyItem?.fides_key!)}
      onMouseLeave={() => onMouseLeave(taxonomyItem?.fides_key!)}
    >
      <AntButton
        className={`${styles.button} ${getNodeHoverStatusClass()}`}
        onClick={() => onTaxonomyItemClick?.(taxonomyItem!)}
        disabled={!onTaxonomyItemClick}
        type="text"
      >
        <AntTypography.Text ellipsis style={{ color: "inherit" }}>
          {taxonomyItem?.active === false ? "(disabled) " : ""}
          {label}
        </AntTypography.Text>
      </AntButton>

      <TaxonomyTreeNodeHandle
        type="source"
        inactive={nodeHoverStatus === "INACTIVE"}
      />
      <TaxonomyTreeNodeHandle
        type="target"
        inactive={nodeHoverStatus === "INACTIVE"}
      />

      <div className="absolute left-full top-0 pl-2 opacity-0 transition duration-300 group-hover:opacity-100">
        <AntButton
          type="default"
          className={styles["add-button"]}
          icon={<Icons.Add size={20} />}
          onClick={() => onAddButtonClick?.(taxonomyItem)}
          size="middle"
        />
      </div>
    </div>
  );
};
export default TaxonomyTreeNode;
