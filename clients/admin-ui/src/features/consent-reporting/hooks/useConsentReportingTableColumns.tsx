import { createColumnHelper } from "@tanstack/react-table";
import palette from "fidesui/src/palette/palette.module.scss";
import { useMemo } from "react";

import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import {
  BadgeCell,
  DefaultCell,
  DefaultHeaderCell,
} from "~/features/common/table/v2";
import { formatDate } from "~/features/common/utils";
import { ConsentReportingSchema, PrivacyNoticeRegion } from "~/types/api";

import {
  USER_CONSENT_PREFERENCE_COLOR,
  USER_CONSENT_PREFERENCE_LABELS,
} from "../constants";

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
          const region = getValue() as PrivacyNoticeRegion | null | undefined;
          const regionLabel =
            region && PRIVACY_NOTICE_REGION_RECORD[region]
              ? PRIVACY_NOTICE_REGION_RECORD[region]
              : region || "";
          return <DefaultCell value={regionLabel} />;
        },
        header: (props) => (
          <DefaultHeaderCell value="User geography" {...props} />
        ),
        enableSorting: false,
      }),
      columnHelper.accessor((row) => row.preference, {
        id: "preference",
        cell: ({ getValue }) => {
          const preference = getValue();
          const preferenceLabel =
            (preference && USER_CONSENT_PREFERENCE_LABELS[preference]) || "";

          const badgeColor =
            (preference && USER_CONSENT_PREFERENCE_COLOR[preference]) || "";

          return <BadgeCell color={badgeColor} value={preferenceLabel} />;
        },
        header: (props) => <DefaultHeaderCell value="Preference" {...props} />,
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
        header: (props) => <DefaultHeaderCell value="Method" {...props} />,
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
