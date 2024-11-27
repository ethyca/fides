import { Handle, Node, NodeProps, Position } from "@xyflow/react";
import { AntButton, SmallAddIcon } from "fidesui";

import { TaxonomyEntity } from "../types";

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
  const { taxonomyItem, onAddButtonClick, onTaxonomyItemClick, label } = data;

  const handleRadius = 8;
  return (
    <div className="group relative">
      <button
        type="button"
        className="max-w-[300px] cursor-pointer truncate rounded px-4 py-1 transition-colors duration-300 group-hover:bg-black group-hover:text-white"
        onClick={() => onTaxonomyItemClick?.(taxonomyItem!)}
        disabled={!onTaxonomyItemClick}
      >
        {taxonomyItem?.active === false ? "(disabled) " : ""}
        {label}
      </button>

      <Handle
        type="target"
        position={Position.Left}
        style={{ width: handleRadius, height: handleRadius }}
      />
      <Handle
        type="source"
        position={Position.Right}
        style={{ width: handleRadius, height: handleRadius }}
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
