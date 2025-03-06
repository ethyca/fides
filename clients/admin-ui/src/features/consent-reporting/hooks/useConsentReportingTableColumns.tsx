import { createColumnHelper } from "@tanstack/react-table";
import palette from "fidesui/src/palette/palette.module.scss";
import { useMemo } from "react";

import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import { DefaultCell, DefaultHeaderCell } from "~/features/common/table/v2";
import { formatDate } from "~/features/common/utils";
import { ConsentReportingSchema, PrivacyNoticeRegion } from "~/types/api";

const columnHelper = createColumnHelper<ConsentReportingSchema>();

const useConsentReportingTableColumns = () => {
  const columns = useMemo(
    () => [
      columnHelper.accessor((row) => row.email, {
        id: "email",
        cell: ({ getValue }) => (
          <DefaultCell
            value={
              <a
                href={`mailto:${getValue()}`}
                style={{ color: palette.FIDESUI_LINK }}
              >
                {getValue()}
              </a>
            }
          />
        ),
        header: (props) => <DefaultHeaderCell value="Email" {...props} />,
        enableSorting: false,
      }),
      columnHelper.accessor((row) => row.user_geography, {
        id: "user_geography",
        cell: ({ getValue }) => {
          const region = getValue();
          return (
            <DefaultCell
              value={
                region &&
                PRIVACY_NOTICE_REGION_RECORD[region as PrivacyNoticeRegion]
                  ? PRIVACY_NOTICE_REGION_RECORD[region as PrivacyNoticeRegion]
                  : region
              }
            />
          );
        },
        header: (props) => (
          <DefaultHeaderCell value="User geography" {...props} />
        ),
        enableSorting: false,
      }),
      columnHelper.accessor((row) => row.preference, {
        id: "preference",
        cell: ({ getValue }) => <DefaultCell value={getValue()} />,
        header: (props) => <DefaultHeaderCell value="Preference" {...props} />,
        enableSorting: false,
      }),
      columnHelper.accessor((row) => row.tcf_preferences, {
        id: "tcf_preferences",
        cell: ({ getValue }) => <DefaultCell value={getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="TCF Preference" {...props} />
        ),
        enableSorting: false,
      }),
      columnHelper.accessor((row) => row.privacy_notice_history_id, {
        id: "privacy_notice_history_id",
        cell: ({ getValue }) => <DefaultCell value={getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Privacy notice" {...props} />
        ),
        enableSorting: false,
      }),
      columnHelper.accessor((row) => row.method, {
        id: "method",
        cell: ({ getValue }) => <DefaultCell value={getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Privacy notice" {...props} />
        ),
        enableSorting: false,
      }),
      columnHelper.accessor((row) => row.request_origin, {
        id: "request_origin",
        cell: ({ getValue }) => <DefaultCell value={getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Request origin" {...props} />
        ),
        enableSorting: false,
      }),
      columnHelper.accessor((row) => row.request_timestamp, {
        id: "request_timestamp",
        cell: ({ getValue }) => <DefaultCell value={formatDate(getValue())} />,
        header: (props) => (
          <DefaultHeaderCell value="Request timestamp" {...props} />
        ),
      }),
      columnHelper.accessor((row) => row.id, {
        id: "id",
        cell: ({ getValue }) => <DefaultCell value={getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Preference ID" {...props} />
        ),
        enableSorting: false,
      }),
    ],
    [],
  );

  return columns;
};
export default useConsentReportingTableColumns;
