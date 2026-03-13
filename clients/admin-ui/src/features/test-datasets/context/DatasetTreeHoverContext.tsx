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
  CHILD_OF_HOVER = "CHILD_OF_HOVER",
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

  const getDescendants = (nodeId: string): Set<string> => {
    const descendants = new Set<string>();
    // children: parent → children[]
    const children = new Map<string, string[]>();
    edges.forEach((e) => {
      if (!children.has(e.source)) {
        children.set(e.source, []);
      }
      children.get(e.source)!.push(e.target);
    });
    const stack = children.get(nodeId) ?? [];
    while (stack.length > 0) {
      const child = stack.pop()!;
      descendants.add(child);
      const grandchildren = children.get(child);
      if (grandchildren) {
        stack.push(...grandchildren);
      }
    }
    return descendants;
  };

  return { getAncestors, getDescendants };
};

export const DatasetTreeHoverProvider = ({
  edges,
  children,
}: {
  edges: Edge[];
  children: ReactNode;
}) => {
  const [activeNodeId, setActiveNodeId] = useState<string | null>(null);

  const { getAncestors, getDescendants } = useMemo(
    () => buildAncestryMaps(edges),
    [edges],
  );

  const onMouseEnter = useCallback(
    (nodeId: string) => {
      if (nodeId !== activeNodeId) {
        setActiveNodeId(nodeId);
      }
    },
    [activeNodeId],
  );

  const onMouseLeave = useCallback(() => {
    setActiveNodeId(null);
  }, []);

  const getNodeHoverStatus = useCallback(
    (nodeId: string): DatasetNodeHoverStatus => {
      if (!activeNodeId) {
        return DatasetNodeHoverStatus.DEFAULT;
      }

      if (nodeId === activeNodeId) {
        return DatasetNodeHoverStatus.ACTIVE_HOVER;
      }

      // Is this node an ancestor of the hovered node?
      const ancestors = getAncestors(activeNodeId);
      if (ancestors.has(nodeId)) {
        return DatasetNodeHoverStatus.PARENT_OF_HOVER;
      }

      // Is this node a descendant of the hovered node?
      const descendants = getDescendants(activeNodeId);
      if (descendants.has(nodeId)) {
        return DatasetNodeHoverStatus.CHILD_OF_HOVER;
      }

      return DatasetNodeHoverStatus.INACTIVE;
    },
    [activeNodeId, getAncestors, getDescendants],
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
