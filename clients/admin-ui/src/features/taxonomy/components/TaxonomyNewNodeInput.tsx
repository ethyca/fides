import { Handle, Position } from "@xyflow/react";
import { AntInput } from "fidesui";

const TaxonomyNewNodeInput = () => {
  return (
    <div className="bg-red w-[200px]">
      <AntInput />
      <Handle type="target" position={Position.Left} />
    </div>
  );
};
export default TaxonomyNewNodeInput;
