import { Handle, HandleType, Position } from "@xyflow/react";

interface TaxonomyTreeNodeHandleProps {
  type: HandleType;
  inactive?: boolean;
}

const TaxonomyTreeNodeHandle = ({
  type,
  inactive = false,
}: TaxonomyTreeNodeHandleProps) => {
  const handleRadius = 8;

  return (
    <Handle
      type={type}
      position={type === "source" ? Position.Right : Position.Left}
      style={{
        width: handleRadius,
        height: handleRadius,
        backgroundColor: inactive ? "#a0aec0" : "black",
      }}
      className="transition-colors duration-300"
    />
  );
};
export default TaxonomyTreeNodeHandle;
