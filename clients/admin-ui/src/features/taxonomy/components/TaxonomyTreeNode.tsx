import { Handle, Node, NodeProps, Position } from "@xyflow/react";
import { AntButton, SmallAddIcon } from "fidesui";
import { useCallback, useContext } from "react";

import { TaxonomyTreeHoverContext } from "../context/TaxonomyTreeHoverContext";
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
      case "ACTIVE_HOVER":
        return styles["button-hover"];
      case "PATH_HOVER":
        return styles["button-path-hover"];
      case "INACTIVE":
        return styles["button-inactive"];
      default:
        return "";
    }
  }, [nodeHoverStatus]);

  return (
    <div
      className="relative"
      onMouseEnter={() => onMouseEnter(taxonomyItem?.fides_key!)}
      onMouseLeave={() => onMouseLeave(taxonomyItem?.fides_key!)}
    >
      <button
        type="button"
        className={`${styles.button} ${getNodeHoverStatusClass()}`}
        onClick={() => onTaxonomyItemClick?.(taxonomyItem!)}
        disabled={!onTaxonomyItemClick}
      >
        {taxonomyItem?.active === false ? "(disabled) " : ""}
        {label}
      </button>

      <TaxonomyTreeNodeHandle
        type="source"
        inactive={nodeHoverStatus === "INACTIVE"}
      />
      <TaxonomyTreeNodeHandle
        type="target"
        inactive={nodeHoverStatus === "INACTIVE"}
      />

      <div className=" absolute left-full top-0 pl-2 opacity-0 transition duration-300 group-hover:opacity-100">
        <AntButton
          type="default"
          className="bg-white pt-0.5 shadow-[0_1px_3px_0px_rgba(0,0,0,0.1)] "
          icon={<SmallAddIcon className="text-xl" />}
          onClick={() => onAddButtonClick?.(taxonomyItem)}
        />
      </div>
    </div>
  );
};
export default TaxonomyTreeNode;
