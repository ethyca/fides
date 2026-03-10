import { ColumnsType, Tag } from "fidesui";
import { useMemo } from "react";

import { useAntTable, useTableState } from "~/features/common/table/hooks";
import { PreferencesSaved, UserConsentPreference } from "~/types/api";

import {
  USER_CONSENT_PREFERENCE_COLOR,
  USER_CONSENT_PREFERENCE_LABELS,
} from "../constants";

export interface TcfDetailRow {
  key: string;
  id: string | number;
  preference: UserConsentPreference;
}

// Transform preferences data to table rows
export const mapTcfPreferencesToRowColumns = (
  allPreferences?: PreferencesSaved | null,
): TcfDetailRow[] => {
  const results: TcfDetailRow[] = [];
  if (allPreferences) {
    const { preferences, ...tcfFields } = allPreferences;
    Object.entries(tcfFields).forEach(([key, records]) => {
      if (records && Array.isArray(records)) {
        records.forEach((value) => {
          results.push({
            key,
            id: value.id,
            preference: value.preference,
          });
        });
      }
    });
  }
  return results;
};

// Filter out system and vendor preferences
export const filterTcfConsentPreferences = (
  preferences: TcfDetailRow[],
): TcfDetailRow[] => {
  return preferences.filter((row) => {
    const isSystemOrVendorPreference =
      row.key.startsWith("system_") || row.key.startsWith("vendor_");
    return !isSystemOrVendorPreference;
  });
};

const useTcfConsentTable = (tcfPreferences?: PreferencesSaved | null) => {
  // Transform and filter data
  const tcfData = mapTcfPreferencesToRowColumns(tcfPreferences);
  const filteredTcfData = filterTcfConsentPreferences(tcfData);

  // Table state management with URL state disabled for modals
  const tableState = useTableState({
    disableUrlState: true,
  });

  // Ant table configuration
  const { tableProps } = useAntTable(tableState, {
    dataSource: filteredTcfData,
    totalRows: filteredTcfData.length,
    isLoading: false,
    getRowKey: (record: TcfDetailRow) => `${record.key}-${record.id}`,
    customTableProps: {
      size: "small",
    },
  });

  // Column definitions
  const columns: ColumnsType<TcfDetailRow> = useMemo(
    () => [
      {
        title: "Type",
        dataIndex: "key",
        key: "key",
        render: (value: string) => value,
      },
      {
        title: "ID",
        dataIndex: "id",
        key: "id",
        render: (value: string | number) => value,
      },
      {
        title: "Preference",
        dataIndex: "preference",
        key: "preference",
        width: 100,
        render: (preference: UserConsentPreference) => {
          const label =
            USER_CONSENT_PREFERENCE_LABELS[preference] || preference;
          const color = USER_CONSENT_PREFERENCE_COLOR[preference] || "";
          return <Tag color={color}>{label}</Tag>;
        },
      },
    ],
    [],
  );

  return {
    tableProps,
    columns,
  };
};

export default useTcfConsentTable;
