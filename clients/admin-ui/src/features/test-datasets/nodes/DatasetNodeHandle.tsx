import { Handle, HandleType, Position } from "@xyflow/react";
import palette from "fidesui/src/palette/palette.module.scss";

interface DatasetNodeHandleProps {
  type: HandleType;
  inactive?: boolean;
}

const DatasetNodeHandle = ({
  type,
  inactive = false,
}: DatasetNodeHandleProps) => (
  <Handle
    type={type}
    position={type === "source" ? Position.Right : Position.Left}
    style={{
      width: 8,
      height: 8,
      backgroundColor: inactive
        ? palette.FIDESUI_NEUTRAL_400
        : palette.FIDESUI_MINOS,
    }}
    className="transition-colors duration-300 ease-in"
  />
);

export default DatasetNodeHandle;
