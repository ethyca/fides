import { createColumnHelper } from "@tanstack/react-table";
import { useMemo } from "react";

import {
  BadgeCell,
  DefaultCell,
  DefaultHeaderCell,
} from "~/features/common/table/v2";
import { PreferenceWithNoticeInformation } from "~/types/api";

import {
  USER_CONSENT_PREFERENCE_COLOR,
  USER_CONSENT_PREFERENCE_LABELS,
} from "../constants";

const columnHelper = createColumnHelper<PreferenceWithNoticeInformation>();

const useConsentLookupTableColumns = () => {
  const columns = useMemo(
    () => [
      columnHelper.accessor((row) => row.notice_id, {
        id: "notice_id",
        cell: ({ getValue }) => <DefaultCell value={getValue()} />,
        header: (props) => <DefaultHeaderCell value="Notice Id" {...props} />,
        enableSorting: false,
      }),
      columnHelper.accessor((row) => row.notice_key, {
        id: "notice_key",
        cell: ({ getValue }) => <DefaultCell value={getValue()} />,
        header: (props) => <DefaultHeaderCell value="Notice Key" {...props} />,
        enableSorting: false,
      }),
      columnHelper.accessor((row) => row.preference, {
        id: "preference",
        cell: ({ getValue }) => {
          const preference = getValue();
          const preferenceLabel =
            (preference && USER_CONSENT_PREFERENCE_LABELS[preference]) ||
            preference;

          const badgeColor =
            (preference && USER_CONSENT_PREFERENCE_COLOR[preference]) || "";

          return <BadgeCell color={badgeColor} value={preferenceLabel} />;
        },
        header: (props) => <DefaultHeaderCell value="Preference" {...props} />,
        enableSorting: false,
        size: 100,
      }),
      columnHelper.accessor((row) => row.privacy_notice_history_id, {
        id: "privacy_notice_history_id",
        cell: ({ getValue }) => <DefaultCell value={getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Privacy Notice History Id" {...props} />
        ),
        enableSorting: false,
      }),
    ],
    [],
  );

  return columns;
};
export default useConsentLookupTableColumns;
