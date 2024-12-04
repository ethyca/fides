import {
  createContext,
  ReactNode,
  useCallback,
  useMemo,
  useState,
} from "react";

interface TaxonomyTreeHoverContextType {
  activeNodeKey: string | null;
  setActiveNodeKey: (key: string | null) => void;
  onMouseEnter: (fidesKey: string) => void;
  onMouseLeave: (fidesKey: string) => void;
}

export const TaxonomyTreeHoverContext =
  createContext<TaxonomyTreeHoverContextType>({
    activeNodeKey: null,
    setActiveNodeKey: () => {},
    onMouseEnter: () => {},
    onMouseLeave: () => {},
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

  const value = useMemo(
    () => ({ activeNodeKey, setActiveNodeKey, onMouseEnter, onMouseLeave }),
    [activeNodeKey, setActiveNodeKey, onMouseEnter, onMouseLeave],
  );

  return (
    <TaxonomyTreeHoverContext.Provider value={value}>
      {children}
    </TaxonomyTreeHoverContext.Provider>
  );
};
