import { Edge } from "@xyflow/react";
import {
  createContext,
  ReactNode,
  useCallback,
  useMemo,
  useState,
} from "react";

export enum DatasetNodeHoverStatus {
  DEFAULT = "DEFAULT",
  ACTIVE_HOVER = "ACTIVE_HOVER",
  PARENT_OF_HOVER = "PARENT_OF_HOVER",
  INACTIVE = "INACTIVE",
}

interface DatasetTreeHoverContextType {
  activeNodeId: string | null;
  onMouseEnter: (nodeId: string) => void;
  onMouseLeave: () => void;
  getNodeHoverStatus: (nodeId: string) => DatasetNodeHoverStatus;
}

export const DatasetTreeHoverContext =
  createContext<DatasetTreeHoverContextType>({
    activeNodeId: null,
    onMouseEnter: () => {},
    onMouseLeave: () => {},
    getNodeHoverStatus: () => DatasetNodeHoverStatus.DEFAULT,
  });

/**
 * Build ancestor and descendant sets from the edge list so hover
 * highlighting correctly flows through the full path to the root.
 */
const buildAncestryMaps = (edges: Edge[]) => {
  // parentOf: child → parent
  const parentOf = new Map<string, string>();
  edges.forEach((e) => {
    parentOf.set(e.target, e.source);
  });

  const getAncestors = (nodeId: string): Set<string> => {
    const ancestors = new Set<string>();
    let current = parentOf.get(nodeId);
    while (current) {
      ancestors.add(current);
      current = parentOf.get(current);
    }
    return ancestors;
  };

  return { getAncestors };
};

export const DatasetTreeHoverProvider = ({
  edges,
  children,
}: {
  edges: Edge[];
  children: ReactNode;
}) => {
  const [activeNodeId, setActiveNodeId] = useState<string | null>(null);

  const { getAncestors } = useMemo(
    () => buildAncestryMaps(edges),
    [edges],
  );

  const onMouseEnter = useCallback((nodeId: string) => {
    setActiveNodeId((prev) => (prev === nodeId ? prev : nodeId));
  }, []);

  const onMouseLeave = useCallback(() => {
    setActiveNodeId(null);
  }, []);

  // Precompute ancestor/descendant sets once per hover change
  const ancestorSet = useMemo(
    () => (activeNodeId ? getAncestors(activeNodeId) : new Set<string>()),
    [activeNodeId, getAncestors],
  );
  const getNodeHoverStatus = useCallback(
    (nodeId: string): DatasetNodeHoverStatus => {
      if (!activeNodeId) {
        return DatasetNodeHoverStatus.DEFAULT;
      }

      if (nodeId === activeNodeId) {
        return DatasetNodeHoverStatus.ACTIVE_HOVER;
      }

      if (ancestorSet.has(nodeId)) {
        return DatasetNodeHoverStatus.PARENT_OF_HOVER;
      }

      return DatasetNodeHoverStatus.INACTIVE;
    },
    [activeNodeId, ancestorSet],
  );

  const value = useMemo(
    () => ({
      activeNodeId,
      onMouseEnter,
      onMouseLeave,
      getNodeHoverStatus,
    }),
    [activeNodeId, onMouseEnter, onMouseLeave, getNodeHoverStatus],
  );

  return (
    <DatasetTreeHoverContext.Provider value={value}>
      {children}
    </DatasetTreeHoverContext.Provider>
  );
};
