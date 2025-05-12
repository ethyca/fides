import {
  createContext,
  Dispatch,
  SetStateAction,
  useContext,
  useMemo,
} from "react";

import { useLocalStorage } from "~/features/common/hooks/useLocalStorage";
import { DATAMAP_GROUPING } from "~/types/api";

import { DatamapReportFilterSelections } from "../types";
import { COLUMN_IDS, DATAMAP_LOCAL_STORAGE_KEYS } from "./constants";

export const DEFAULT_COLUMN_VISIBILITY = {
  [COLUMN_IDS.SYSTEM_UNDECLARED_DATA_CATEGORIES]: false,
  [COLUMN_IDS.DATA_USE_UNDECLARED_DATA_CATEGORIES]: false,
};

export const DEFAULT_COLUMN_FILTERS = {
  dataUses: [],
  dataSubjects: [],
  dataCategories: [],
};

interface DatamapReportContextProps {
  savedCustomReportId: string;
  setSavedCustomReportId: Dispatch<SetStateAction<string>>;
  groupBy: DATAMAP_GROUPING;
  setGroupBy: Dispatch<SetStateAction<DATAMAP_GROUPING>>;
  selectedFilters: DatamapReportFilterSelections;
  setSelectedFilters: Dispatch<SetStateAction<DatamapReportFilterSelections>>;
  columnOrder: string[];
  setColumnOrder: Dispatch<SetStateAction<string[]>>;
  columnVisibility: Record<string, boolean>;
  setColumnVisibility: Dispatch<SetStateAction<Record<string, boolean>>>;
  columnSizing: Record<string, number>;
  setColumnSizing: Dispatch<SetStateAction<Record<string, number>>>;
  columnNameMapOverrides: Record<string, string>;
  setColumnNameMapOverrides: Dispatch<SetStateAction<Record<string, string>>>;
}

export const DatamapReportContext = createContext<DatamapReportContextProps>(
  {} as DatamapReportContextProps,
);

export const DatamapReportProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const [savedCustomReportId, setSavedCustomReportId] = useLocalStorage<string>(
    DATAMAP_LOCAL_STORAGE_KEYS.CUSTOM_REPORT_ID,
    "",
  );

  const [groupBy, setGroupBy] = useLocalStorage<DATAMAP_GROUPING>(
    DATAMAP_LOCAL_STORAGE_KEYS.GROUP_BY,
    DATAMAP_GROUPING.SYSTEM_DATA_USE,
  );

  const [selectedFilters, setSelectedFilters] =
    useLocalStorage<DatamapReportFilterSelections>(
      DATAMAP_LOCAL_STORAGE_KEYS.FILTERS,
      DEFAULT_COLUMN_FILTERS,
    );

  const [columnOrder, setColumnOrder] = useLocalStorage<string[]>(
    DATAMAP_LOCAL_STORAGE_KEYS.COLUMN_ORDER,
    [],
  );

  const [columnVisibility, setColumnVisibility] = useLocalStorage<
    Record<string, boolean>
  >(DATAMAP_LOCAL_STORAGE_KEYS.COLUMN_VISIBILITY, DEFAULT_COLUMN_VISIBILITY);

  const [columnSizing, setColumnSizing] = useLocalStorage<
    Record<string, number>
  >(DATAMAP_LOCAL_STORAGE_KEYS.COLUMN_SIZING, {});

  const [columnNameMapOverrides, setColumnNameMapOverrides] = useLocalStorage<
    Record<string, string>
  >(DATAMAP_LOCAL_STORAGE_KEYS.COLUMN_NAMES, {});

  const contextValue: DatamapReportContextProps = useMemo(
    () => ({
      savedCustomReportId,
      setSavedCustomReportId,
      groupBy,
      setGroupBy,
      selectedFilters,
      setSelectedFilters,
      columnOrder,
      setColumnOrder,
      columnVisibility,
      setColumnVisibility,
      columnSizing,
      setColumnSizing,
      columnNameMapOverrides,
      setColumnNameMapOverrides,
    }),
    [
      savedCustomReportId,
      setSavedCustomReportId,
      groupBy,
      setGroupBy,
      selectedFilters,
      setSelectedFilters,
      columnOrder,
      setColumnOrder,
      columnVisibility,
      setColumnVisibility,
      columnSizing,
      setColumnSizing,
      columnNameMapOverrides,
      setColumnNameMapOverrides,
    ],
  );

  return (
    <DatamapReportContext.Provider value={contextValue}>
      {children}
    </DatamapReportContext.Provider>
  );
};

/**
 * Note: All values stored in local storage.
 */
export const useDatamapReport = () => {
  const context = useContext(DatamapReportContext);
  if (!context || Object.keys(context).length === 0) {
    throw new Error(
      "useDatamapReport must be used within a DatamapReportProvider",
    );
  }
  return context;
};
