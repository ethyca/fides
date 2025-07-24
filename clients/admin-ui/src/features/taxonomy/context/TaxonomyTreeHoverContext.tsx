import {
  createContext,
  ReactNode,
  useCallback,
  useMemo,
  useState,
} from "react";

import { TAXONOMY_ROOT_NODE_ID } from "../constants";

interface TaxonomyTreeHoverContextType {
  activeNodeKey: string | null;
  setActiveNodeKey: (key: string | null) => void;
  onMouseEnter: (fidesKey: string) => void;
  onMouseLeave: (fidesKey: string) => void;
  getNodeHoverStatus: (fidesKey: string) => TreeNodeHoverStatus;
}

export enum TreeNodeHoverStatus {
  DEFAULT = "DEFAULT", // Node in default state, no hover in any node
  ACTIVE_HOVER = "ACTIVE_HOVER", // This node is hovered
  PARENT_OF_HOVER = "PARENT_OF_HOVER", // This node is a child of the active hovered node
  CHILD_OF_HOVER = "CHILD_OF_HOVER", // This node is a parent of the active hovered node
  SIBLING_OF_HOVER = "SIBLING_OF_HOVER", // This node is a sibling of the active hovered node
  INACTIVE = "INACTIVE", // There's an active hover, but it's not this node and this node is not in the path
}

export const TaxonomyTreeHoverContext =
  createContext<TaxonomyTreeHoverContextType>({
    activeNodeKey: null,
    setActiveNodeKey: () => {},
    onMouseEnter: () => {},
    onMouseLeave: () => {},
    getNodeHoverStatus: () => TreeNodeHoverStatus.DEFAULT,
  });

export const TaxonomyTreeHoverProvider = ({
  children,
}: {
  children: ReactNode;
}) => {
  // Active hover node
  const [activeNodeKey, setActiveNodeKey] = useState<string | null>(null);
  const onMouseEnter = useCallback(
    (fidesKey: string) => {
      if (fidesKey !== activeNodeKey) {
        setActiveNodeKey(fidesKey);
      }
    },
    [activeNodeKey],
  );
  const onMouseLeave = useCallback(() => {
    setActiveNodeKey(null);
  }, []);

  const getNodeHoverStatus = useCallback(
    (fidesKey: string): TreeNodeHoverStatus => {
      if (!activeNodeKey) {
        return TreeNodeHoverStatus.DEFAULT;
      }

      if (fidesKey === activeNodeKey) {
        return TreeNodeHoverStatus.ACTIVE_HOVER;
      }

      if (
        activeNodeKey.startsWith(`${fidesKey}.`) ||
        fidesKey === TAXONOMY_ROOT_NODE_ID
      ) {
        return TreeNodeHoverStatus.PARENT_OF_HOVER;
      }

      if (
        fidesKey.startsWith(`${activeNodeKey}.`) ||
        activeNodeKey === TAXONOMY_ROOT_NODE_ID
      ) {
        return TreeNodeHoverStatus.CHILD_OF_HOVER;
      }

      const activeNodeKeyParts = activeNodeKey.split(".");
      if (
        activeNodeKeyParts.slice(0, -1).join(".") ===
        fidesKey.split(".").slice(0, -1).join(".")
      ) {
        return TreeNodeHoverStatus.SIBLING_OF_HOVER;
      }

      return TreeNodeHoverStatus.INACTIVE;
    },
    [activeNodeKey],
  );

  const value = useMemo(
    () => ({
      activeNodeKey,
      setActiveNodeKey,
      onMouseEnter,
      onMouseLeave,
      getNodeHoverStatus,
    }),
    [
      activeNodeKey,
      setActiveNodeKey,
      onMouseEnter,
      onMouseLeave,
      getNodeHoverStatus,
    ],
  );

  return (
    <TaxonomyTreeHoverContext.Provider value={value}>
      {children}
    </TaxonomyTreeHoverContext.Provider>
  );
};
