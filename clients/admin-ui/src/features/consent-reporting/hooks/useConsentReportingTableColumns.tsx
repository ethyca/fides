import { createColumnHelper } from "@tanstack/react-table";
import {
  AntTag as Tag,
  AntTypography as Typography,
  formatIsoLocation,
  Icons,
  isoStringToEntry,
} from "fidesui";
import { useMemo } from "react";

import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import {
  BadgeCell,
  DefaultCell,
  DefaultHeaderCell,
} from "~/features/common/table/v2";
import { RelativeTimestampCell } from "~/features/common/table/v2/cells";
import {
  ConsentReportingSchema,
  PrivacyNoticeRegion,
  UserConsentPreference,
} from "~/types/api";

import {
  CONSENT_METHOD_LABELS,
  REQUEST_ORIGIN_LABELS,
  USER_CONSENT_PREFERENCE_COLOR,
  USER_CONSENT_PREFERENCE_LABELS,
} from "../constants";

const columnHelper = createColumnHelper<ConsentReportingSchema>();

const useConsentReportingTableColumns = ({
  onTcfDetailViewClick,
}: {
  onTcfDetailViewClick: (preferences: UserConsentPreference) => void;
}) => {
  const columns = useMemo(
    () => [
      columnHelper.accessor((row) => row.fides_user_device_id, {
        id: "fides_user_device_id",
        cell: ({ getValue }) => <DefaultCell value={getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="User device ID" {...props} />
        ),
        enableSorting: false,
      }),
      columnHelper.accessor((row) => row.user_geography, {
        id: "user_geography",
        cell: ({ getValue }) => {
          const region = getValue() as PrivacyNoticeRegion | null | undefined;
          const isoEntry = region && isoStringToEntry(region);
          const legacyEntry =
            (region && PRIVACY_NOTICE_REGION_RECORD[region]) || region;
          const regionLabel = isoEntry
            ? formatIsoLocation({ isoEntry })
            : legacyEntry;

          return <DefaultCell value={regionLabel} />;
        },
        header: (props) => (
          <DefaultHeaderCell value="User geography" {...props} />
        ),
        enableSorting: false,
      }),
      columnHelper.accessor((row) => row.preference, {
        id: "preference",
        cell: ({ getValue, row }) => {
          const preference = getValue();
          const preferenceLabel =
            (preference && USER_CONSENT_PREFERENCE_LABELS[preference]) ||
            preference;

          const badgeColor =
            (preference && USER_CONSENT_PREFERENCE_COLOR[preference]) ||
            undefined;

          const hasTcfDetails =
            preference === "tcf" && row.original.tcf_preferences;

          return hasTcfDetails ? (
            <Tag
              color={badgeColor}
              closeIcon={<Icons.Information />}
              closeButtonLabel="View details"
              onClose={() =>
                onTcfDetailViewClick(row.original.tcf_preferences!)
              }
            >
              {preferenceLabel}
            </Tag>
          ) : (
            <BadgeCell color={badgeColor} value={preferenceLabel} />
          );
        },
        header: (props) => <DefaultHeaderCell value="Preference" {...props} />,
        enableSorting: false,
        size: 100,
      }),
      columnHelper.accessor((row) => row.notice_name, {
        id: "notice_name",
        cell: ({ getValue }) => {
          const value = getValue();
          const label = value === "tcf" ? value.toUpperCase() : value;
          return <DefaultCell value={label} />;
        },
        header: (props) => (
          <DefaultHeaderCell value="Privacy notice" {...props} />
        ),
        enableSorting: false,
      }),
      columnHelper.accessor((row) => row.method, {
        id: "method",
        cell: ({ getValue }) => {
          const method = getValue();
          const methodLabel =
            (method && CONSENT_METHOD_LABELS[method]) || method;
          return <DefaultCell value={methodLabel} />;
        },
        header: (props) => <DefaultHeaderCell value="Method" {...props} />,
        enableSorting: false,
        size: 100,
      }),
      columnHelper.accessor((row) => row.request_origin, {
        id: "request_origin",
        cell: ({ getValue }) => {
          const requestOrigin = getValue();
          const requestOriginLabel =
            (requestOrigin && REQUEST_ORIGIN_LABELS[requestOrigin]) ||
            requestOrigin;

          return <DefaultCell value={requestOriginLabel} />;
        },
        header: (props) => (
          <DefaultHeaderCell value="Request origin" {...props} />
        ),
        enableSorting: false,
        size: 120,
      }),
      columnHelper.accessor((row) => row.request_timestamp, {
        id: "request_timestamp",
        cell: ({ getValue }) => <RelativeTimestampCell time={getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Request timestamp" {...props} />
        ),
        size: 120,
      }),
      columnHelper.accessor((row) => row.url_recorded, {
        id: "url_recorded",
        cell: ({ getValue }) => <DefaultCell value={getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Recorded URL" {...props} />
        ),
      }),
      columnHelper.accessor((row) => row.external_id, {
        id: "external_id",
        cell: ({ getValue }) => <DefaultCell value={getValue()} />,
        header: (props) => <DefaultHeaderCell value="External ID" {...props} />,
        enableSorting: false,
      }),
      columnHelper.accessor((row) => row.email, {
        id: "email",
        cell: ({ getValue }) => (
          <DefaultCell
            value={
              <Typography.Link href={`mailto:${getValue()}`}>
                {getValue()}
              </Typography.Link>
            }
          />
        ),
        header: (props) => <DefaultHeaderCell value="Email" {...props} />,
        enableSorting: false,
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
    [onTcfDetailViewClick],
  );

  return columns;
};
export default useConsentReportingTableColumns;
