import { ColumnsType, Tag } from "fidesui";
import { useMemo } from "react";

import { useAntTable, useTableState } from "~/features/common/table/hooks";
import {
  PreferenceWithNoticeInformation,
  UserConsentPreference,
} from "~/types/api";

import {
  USER_CONSENT_PREFERENCE_COLOR,
  USER_CONSENT_PREFERENCE_LABELS,
} from "../constants";

const useConsentLookupTable = (
  preferences?: PreferenceWithNoticeInformation[],
) => {
  // Table state with URL state disabled for modals
  const tableState = useTableState({
    disableUrlState: true,
  });

  // Ant table configuration
  const { tableProps } = useAntTable(tableState, {
    dataSource: preferences || [],
    totalRows: preferences?.length || 0,
    isLoading: false,
    getRowKey: (record: PreferenceWithNoticeInformation) =>
      `${record.privacy_notice_history_id}`,
    customTableProps: {
      size: "small",
    },
  });

  // Column definitions
  const columns: ColumnsType<PreferenceWithNoticeInformation> = useMemo(
    () => [
      {
        title: "Privacy notice",
        dataIndex: "notice_name",
        key: "notice_name",
        render: (value: string) => value,
      },
      {
        title: "Notice Key",
        dataIndex: "notice_key",
        key: "notice_key",
        render: (value: string) => value,
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
      {
        title: "Privacy Notice History Id",
        dataIndex: "privacy_notice_history_id",
        key: "privacy_notice_history_id",
        render: (value: string) => value,
      },
    ],
    [],
  );

  return {
    tableProps,
    columns,
  };
};

export default useConsentLookupTable;
