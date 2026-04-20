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
        backgroundColor: inactive
          ? "var(--fidesui-neutral-400)"
          : "var(--fidesui-minos)",
      }}
      className="transition-colors duration-300 ease-in"
    />
  );
};
export default TaxonomyTreeNodeHandle;
