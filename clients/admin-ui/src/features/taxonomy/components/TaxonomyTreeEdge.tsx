import { BezierEdge, BezierEdgeProps } from "@xyflow/react";
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
        return "var(--fidesui-brand-minos)";
      case TreeNodeHoverStatus.INACTIVE:
        return "var(--fidesui-neutral-400)";
      default:
        return "var(--fidesui-brand-sandstone)";
    }
  }, [targetNodeHoverStatus]);

  const getStrokeWidth = useCallback(() => {
    switch (targetNodeHoverStatus) {
      case TreeNodeHoverStatus.ACTIVE_HOVER:
      case TreeNodeHoverStatus.PARENT_OF_HOVER:
        return 2;
      default:
        return 1;
    }
  }, [targetNodeHoverStatus]);

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
export default TaxonomyTreeEdge;
