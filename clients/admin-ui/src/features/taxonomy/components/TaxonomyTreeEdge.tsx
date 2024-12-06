import { BezierEdge, BezierEdgeProps } from "@xyflow/react";
import palette from "fidesui/src/palette/palette.module.scss";
import { useCallback, useContext } from "react";

import {
  TaxonomyTreeHoverContext,
  TreeNodeHoverStatus,
} from "../context/TaxonomyTreeHoverContext";

interface TaxonomyTreeEdgeProps extends BezierEdgeProps {
  target: string;
  source: string;
}

const TaxonomyTreeEdge = (props: TaxonomyTreeEdgeProps) => {
  const { getNodeHoverStatus } = useContext(TaxonomyTreeHoverContext);

  const { target } = props;
  const targetNodeHoverStatus = getNodeHoverStatus(target);

  const getStrokeColor = useCallback(() => {
    switch (targetNodeHoverStatus) {
      case TreeNodeHoverStatus.ACTIVE_HOVER:
      case TreeNodeHoverStatus.PARENT_OF_HOVER:
        return palette.FIDESUI_MINOS;
      case TreeNodeHoverStatus.INACTIVE:
        return palette.NEUTRAL_400;
      default:
        return palette.FIDESUI_SANDSTONE;
    }
  }, [targetNodeHoverStatus]);

  return (
    <BezierEdge
      {...props}
      style={{
        stroke: getStrokeColor(),
        strokeWidth: 1,
        transition: "stroke 0.3s ease 0s",
      }}
    />
  );
};
export default TaxonomyTreeEdge;
