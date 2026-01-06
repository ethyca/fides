import { formatDistance } from "date-fns";
import {
  type ColumnsType,
  formatIsoLocation,
  Icons,
  isoStringToEntry,
  Tag,
  Typography,
} from "fidesui";
import { useMemo } from "react";

import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import { EllipsisCell } from "~/features/common/table/cells";
import {
  ConsentMethod,
  ConsentReportingSchema,
  PrivacyNoticeRegion,
  RequestOrigin,
  UserConsentPreference,
} from "~/types/api";

import {
  CONSENT_METHOD_LABELS,
  REQUEST_ORIGIN_LABELS,
  USER_CONSENT_PREFERENCE_COLOR,
  USER_CONSENT_PREFERENCE_LABELS,
} from "../constants";

const useConsentReportingTableColumns = ({
  onTcfDetailViewClick,
}: {
  onTcfDetailViewClick: (preferences: UserConsentPreference) => void;
}) => {
  const columns: ColumnsType<ConsentReportingSchema> = useMemo(
    () => [
      {
        title: "User device ID",
        dataIndex: "fides_user_device_id",
        key: "fides_user_device_id",
        render: (value: string) => <EllipsisCell>{value}</EllipsisCell>,
      },
      {
        title: "User geography",
        dataIndex: "user_geography",
        key: "user_geography",
        render: (region: PrivacyNoticeRegion | null | undefined) => {
          const isoEntry = region && isoStringToEntry(region);
          const legacyEntry =
            (region && PRIVACY_NOTICE_REGION_RECORD[region]) || region;
          const regionLabel = isoEntry
            ? formatIsoLocation({ isoEntry })
            : legacyEntry;
          return <EllipsisCell>{regionLabel}</EllipsisCell>;
        },
      },
      {
        title: "Preference",
        dataIndex: "preference",
        key: "preference",
        render: (
          preference: UserConsentPreference,
          record: ConsentReportingSchema,
        ) => {
          const preferenceLabel =
            (preference && USER_CONSENT_PREFERENCE_LABELS[preference]) ||
            preference;
          const badgeColor =
            (preference && USER_CONSENT_PREFERENCE_COLOR[preference]) ||
            undefined;
          const hasTcfDetails = preference === "tcf" && record.tcf_preferences;

          return hasTcfDetails ? (
            <Tag
              color={badgeColor}
              closeIcon={<Icons.Information />}
              closeButtonLabel="View details"
              onClose={() => onTcfDetailViewClick(record.tcf_preferences!)}
              data-testid="tcf-badge"
            >
              {preferenceLabel}
            </Tag>
          ) : (
            <Tag color={badgeColor}>{preferenceLabel}</Tag>
          );
        },
      },
      {
        title: "Privacy notice",
        dataIndex: "notice_name",
        key: "notice_name",
        render: (value: string) => {
          const label = value === "tcf" ? value.toUpperCase() : value;
          return <EllipsisCell>{label}</EllipsisCell>;
        },
      },
      {
        title: "Method",
        dataIndex: "method",
        key: "method",
        render: (method: ConsentMethod) => {
          const methodLabel = method ? CONSENT_METHOD_LABELS[method] : method;
          return methodLabel;
        },
      },
      {
        title: "Request origin",
        dataIndex: "request_origin",
        key: "request_origin",
        render: (requestOrigin: RequestOrigin) => {
          const requestOriginLabel = requestOrigin
            ? REQUEST_ORIGIN_LABELS[requestOrigin]
            : requestOrigin;
          return requestOriginLabel;
        },
      },
      {
        title: "Request timestamp",
        dataIndex: "request_timestamp",
        key: "request_timestamp",
        render: (timestamp: string) => {
          if (!timestamp) {
            return "N/A";
          }
          return formatDistance(new Date(timestamp), new Date(), {
            addSuffix: true,
          });
        },
      },
      {
        title: "Recorded URL",
        dataIndex: "url_recorded",
        key: "url_recorded",
        render: (url: string) => <EllipsisCell>{url}</EllipsisCell>,
      },
      {
        title: "External ID",
        dataIndex: "external_id",
        key: "external_id",
        render: (externalId: string) => (
          <EllipsisCell>{externalId}</EllipsisCell>
        ),
      },
      {
        title: "Email",
        dataIndex: "email",
        key: "email",
        render: (email: string) =>
          email ? (
            <Typography.Link href={`mailto:${email}`}>
              <EllipsisCell className="w-36 hover:underline">
                {email}
              </EllipsisCell>
            </Typography.Link>
          ) : null,
      },
      {
        title: "Preference ID",
        dataIndex: "id",
        key: "id",
        render: (id: string) => <EllipsisCell>{id}</EllipsisCell>,
      },
    ],
    [onTcfDetailViewClick],
  );

  return columns;
};

export default useConsentReportingTableColumns;
