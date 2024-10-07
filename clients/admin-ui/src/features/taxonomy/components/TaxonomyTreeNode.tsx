import { Handle, Position } from "@xyflow/react";
import { AntButton, SmallAddIcon } from "fidesui";

import { TaxonomyEntity } from "../types";

interface NodeData {
  label: string;
  taxonomyItem: TaxonomyEntity;
  onTaxonomyItemClick: (taxonomyItem: TaxonomyEntity) => void;
}

const TaxonomyTreeNode = ({ data }: { data: NodeData }) => {
  return (
    <div className="group relative">
      <button
        type="button"
        className=" rounded px-4 py-1 transition-colors group-hover:bg-black group-hover:text-white"
        onClick={() => data.onTaxonomyItemClick?.(data.taxonomyItem!)}
      >
        {data.label}
      </button>

      <Handle type="target" position={Position.Left} />
      <Handle type="source" position={Position.Right} />
      <div className="absolute left-full top-0 hidden pl-2 group-hover:block">
        <AntButton
          type="default"
          className="bg-white pt-0.5 shadow-[0_1px_3px_0px_rgba(0,0,0,0.1)] "
          icon={<SmallAddIcon className="text-xl" />}
        />
      </div>
    </div>
  );
};
export default TaxonomyTreeNode;
