import { BezierEdge, BezierEdgeProps } from "@xyflow/react";
import palette from "fidesui/src/palette/palette.module.scss";
import { useCallback, useContext } from "react";

import {
  DatasetNodeHoverStatus,
  DatasetTreeHoverContext,
} from "../context/DatasetTreeHoverContext";

interface DatasetTreeEdgeProps extends BezierEdgeProps {
  target: string;
}

const DatasetTreeEdge = (props: DatasetTreeEdgeProps) => {
  const { getNodeHoverStatus } = useContext(DatasetTreeHoverContext);
  const { target } = props;
  const targetHoverStatus = getNodeHoverStatus(target);

  const getStrokeColor = useCallback(() => {
    switch (targetHoverStatus) {
      case DatasetNodeHoverStatus.ACTIVE_HOVER:
      case DatasetNodeHoverStatus.PARENT_OF_HOVER:
        return palette.FIDESUI_MINOS;
      case DatasetNodeHoverStatus.INACTIVE:
        return palette.FIDESUI_NEUTRAL_400;
      default:
        return palette.FIDESUI_SANDSTONE;
    }
  }, [targetHoverStatus]);

  const getStrokeWidth = useCallback(() => {
    switch (targetHoverStatus) {
      case DatasetNodeHoverStatus.ACTIVE_HOVER:
      case DatasetNodeHoverStatus.PARENT_OF_HOVER:
        return 2;
      default:
        return 1;
    }
  }, [targetHoverStatus]);

  return (
    <BezierEdge
      {...props}
      style={{
        stroke: getStrokeColor(),
        strokeWidth: getStrokeWidth(),
        transition: "stroke 0.3s ease 0s",
      }}
    />
  );
};

export default DatasetTreeEdge;
