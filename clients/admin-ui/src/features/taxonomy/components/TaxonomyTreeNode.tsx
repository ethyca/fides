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

  // TODO: Differenciate disabled items
  // TODO: set a max width for tree nodes, test how it behaves with layout library
  return (
    <div className="group relative">
      <button
        type="button"
        className="cursor-default rounded px-4 py-1 transition-colors group-hover:bg-black group-hover:text-white"
        onClick={() => onTaxonomyItemClick?.(taxonomyItem!)}
        disabled={!onTaxonomyItemClick}
      >
        {label}
      </button>

      <Handle type="target" position={Position.Left} />
      <Handle type="source" position={Position.Right} />
      <div className="absolute left-full top-0 hidden pl-2 group-hover:block">
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
