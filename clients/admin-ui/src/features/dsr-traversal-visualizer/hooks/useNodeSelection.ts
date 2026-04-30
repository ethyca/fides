import { Node } from "@xyflow/react";
import { useCallback, useState } from "react";

export const useNodeSelection = () => {
  const [selected, setSelected] = useState<Node | null>(null);
  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => setSelected(node),
    [],
  );
  const clear = useCallback(() => setSelected(null), []);
  return { selected, onNodeClick, clear };
};
