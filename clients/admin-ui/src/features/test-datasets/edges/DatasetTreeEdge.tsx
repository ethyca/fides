import { BezierEdge, BezierEdgeProps } from "@xyflow/react";
import palette from "fidesui/src/palette/palette.module.scss";
import { useContext } from "react";

import {
  DatasetNodeHoverStatus,
  DatasetTreeHoverContext,
} from "../context/DatasetTreeHoverContext";

interface DatasetTreeEdgeProps extends BezierEdgeProps {
  target: string;
}

const getStrokeColor = (status: DatasetNodeHoverStatus): string => {
  switch (status) {
    case DatasetNodeHoverStatus.ACTIVE_HOVER:
    case DatasetNodeHoverStatus.PARENT_OF_HOVER:
      return palette.FIDESUI_MINOS;
    case DatasetNodeHoverStatus.INACTIVE:
      return palette.FIDESUI_NEUTRAL_400;
    default:
      return palette.FIDESUI_SANDSTONE;
  }
};

const getStrokeWidth = (status: DatasetNodeHoverStatus): number => {
  switch (status) {
    case DatasetNodeHoverStatus.ACTIVE_HOVER:
    case DatasetNodeHoverStatus.PARENT_OF_HOVER:
      return 2;
    default:
      return 1;
  }
};

const DatasetTreeEdge = (props: DatasetTreeEdgeProps) => {
  const { getNodeHoverStatus } = useContext(DatasetTreeHoverContext);
  const { target } = props;
  const targetHoverStatus = getNodeHoverStatus(target);

  return (
    <BezierEdge
      {...props}
      style={{
        stroke: getStrokeColor(targetHoverStatus),
        strokeWidth: getStrokeWidth(targetHoverStatus),
        transition: "stroke 0.3s ease 0s",
      }}
    />
  );
};

export default DatasetTreeEdge;
