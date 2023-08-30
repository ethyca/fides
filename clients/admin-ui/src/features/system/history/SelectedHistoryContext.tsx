import React, { createContext, useContext, ReactNode } from "react";
import { SystemHistory } from "./system-history.slice";

type FormType = "before" | "after";

interface SelectedHistoryContextProps {
  selectedHistory: SystemHistory | null;
  formType: FormType;
}

const SelectedHistoryContext =
  createContext<SelectedHistoryContextProps | null>(null);

export const useSelectedHistory = () => {
  return useContext(SelectedHistoryContext)!;
};

interface SelectedHistoryProviderProps {
  children: ReactNode;
  selectedHistory: SystemHistory | null;
  formType: FormType;
}

const SelectedHistoryProvider: React.FC<SelectedHistoryProviderProps> = ({
  children,
  selectedHistory,
  formType,
}) => {
  return (
    <SelectedHistoryContext.Provider value={{ selectedHistory, formType }}>
      {children}
    </SelectedHistoryContext.Provider>
  );
};

export default SelectedHistoryProvider;
