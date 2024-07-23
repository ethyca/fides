import React, { createContext, ReactNode, useContext, useMemo } from "react";

import { SystemHistoryResponse } from "~/types/api";

type FormType = "before" | "after";

interface SelectedHistoryContextProps {
  selectedHistory: SystemHistoryResponse | null;
  formType: FormType;
}

const SelectedHistoryContext =
  createContext<SelectedHistoryContextProps | null>(null);

export const useSelectedHistory = () => useContext(SelectedHistoryContext)!;

interface SelectedHistoryProviderProps {
  children: ReactNode;
  selectedHistory: SystemHistoryResponse | null;
  formType: FormType;
}

const SelectedHistoryProvider = ({
  children,
  selectedHistory,
  formType,
}: SelectedHistoryProviderProps) => {
  const value = useMemo(
    () => ({ selectedHistory, formType }),
    [selectedHistory, formType],
  );

  return (
    <SelectedHistoryContext.Provider value={value}>
      {children}
    </SelectedHistoryContext.Provider>
  );
};

export default SelectedHistoryProvider;
