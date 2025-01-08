import { useReactFlow } from "@xyflow/react";
import { useCallback } from "react";

interface UseCenterScreenOnNodeParams {
  positionAbsoluteX: number;
  positionAbsoluteY: number;
  nodeWidth: number;
}

const useCenterScreenOnNode = ({
  positionAbsoluteX,
  positionAbsoluteY,
  nodeWidth,
}: UseCenterScreenOnNodeParams) => {
  const { setCenter, getZoom } = useReactFlow();

  const centerScreenOnNode = useCallback(
    () =>
      setCenter(positionAbsoluteX + nodeWidth / 2, positionAbsoluteY, {
        duration: 500,
        zoom: getZoom(),
      }),
    [getZoom, positionAbsoluteX, positionAbsoluteY, nodeWidth, setCenter],
  );

  return { centerScreenOnNode };
};
export default useCenterScreenOnNode;
