import { Handle, HandleType, Position } from "@xyflow/react";
import palette from "fidesui/src/palette/palette.module.scss";

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
          ? palette.FIDESUI_NEUTRAL_400
          : palette.FIDESUI_MINOS,
      }}
      className="transition-colors duration-300"
    />
  );
};
export default TaxonomyTreeNodeHandle;
