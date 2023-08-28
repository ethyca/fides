import { createContext, useCallback, useContext, useMemo, useRef } from "react";

type ResetCallback = () => void;

type ResetSuggestionField = {
  name: string;
  callback: ResetCallback;
};

const ResetSuggestionContext = createContext<
  | {
      callbacks: ResetSuggestionField[];
      addResetCallback: (resetSuggestionField: ResetSuggestionField) => void;
      removeResetCallback: (fieldName: string) => void;
    }
  | undefined
>(undefined);

export const useResetSuggestionContext = () =>
  useContext(ResetSuggestionContext);

export const ResetSuggestionContextProvider: React.FC = ({ children }) => {
  const callbacks = useRef<ResetSuggestionField[]>([]);
  const addResetCallback = useCallback(
    (resetSuggestionField: ResetSuggestionField) => {
      const idx = callbacks.current
        .map((cb) => cb.name)
        .indexOf(resetSuggestionField.name);
      if (idx > -1) {
        callbacks.current.splice(idx, 1);
      }
      callbacks.current.push(resetSuggestionField);
    },
    []
  );

  const removeResetCallback = useCallback((fieldName: string) => {
    const idx = callbacks.current.map((cb) => cb.name).indexOf(fieldName);
    if (idx > -1) {
      callbacks.current.splice(idx, 1);
    }
  }, []);

  const contextValue = useMemo(
    () => ({
      callbacks: callbacks.current,
      addResetCallback,
      removeResetCallback,
    }),
    [addResetCallback, removeResetCallback]
  );

  return (
    <ResetSuggestionContext.Provider value={contextValue}>
      {children}
    </ResetSuggestionContext.Provider>
  );
};
