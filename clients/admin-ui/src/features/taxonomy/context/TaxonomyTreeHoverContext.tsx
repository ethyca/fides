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
  PATH_HOVER = "PATH_HOVER", // This node is in the path of the hovered node
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
        return TreeNodeHoverStatus.PATH_HOVER;
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
