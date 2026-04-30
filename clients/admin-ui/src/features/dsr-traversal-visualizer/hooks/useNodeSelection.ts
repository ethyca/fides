import { useCallback, useState } from "react";

import { AppNode } from "../types";

export const useNodeSelection = () => {
  const [selected, setSelected] = useState<AppNode | null>(null);
  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: AppNode) => setSelected(node),
    [],
  );
  const clear = useCallback(() => setSelected(null), []);
  return { selected, onNodeClick, clear };
};
