import type { ColumnsType } from "antd/es/table";
import {
  CUSTOM_TAG_COLOR,
  Drawer,
  Flex,
  Table,
  Tag,
  Typography,
} from "fidesui";
import React, { useMemo } from "react";

import { RouterLink } from "~/features/common/nav/RouterLink";
import { PRIVACY_REQUESTS_ROUTE } from "~/features/common/nav/routes";
import { formatDate } from "~/features/common/utils";
import { statusPropMap } from "~/features/privacy-requests/cells";
import { useSearchPrivacyRequestsQuery } from "~/features/privacy-requests/privacy-requests.slice";
import { PrivacyRequestEntity } from "~/features/privacy-requests/types";
import { PrivacyRequestStatus } from "~/types/api";

type RelatedRequestRow = {
  id: string;
  status: PrivacyRequestStatus;
  created_at?: string | null;
  source?: string | null;
};

type RelatedRequestsDrawerProps = {
  isOpen: boolean;
  onClose: () => void;
  privacyRequest: PrivacyRequestEntity;
};

// Builds an `identities` filter payload from the current request's identity
// fields. Empty/null values are excluded so we don't widen the search to
// every request missing that field. The backend OR-matches across fields
// (see filter_privacy_request_queryset), which is what we want for
// "related requests": a later request that adds a phone number still
// surfaces alongside an earlier email-only one from the same person.
const buildIdentitiesFilter = (
  identity: PrivacyRequestEntity["identity"] | undefined,
): Record<string, string> | undefined => {
  if (!identity) {
    return undefined;
  }
  const entries = Object.entries(identity).flatMap(([fieldName, field]) => {
    const value = field?.value;
    if (typeof value !== "string" || value.length === 0) {
      return [];
    }
    return [[fieldName, value]] as const;
  });
  if (entries.length === 0) {
    return undefined;
  }
  return Object.fromEntries(entries);
};

const RelatedRequestsDrawer = ({
  isOpen,
  onClose,
  privacyRequest,
}: RelatedRequestsDrawerProps) => {
  const identitiesFilter = useMemo(
    () => buildIdentitiesFilter(privacyRequest.identity),
    [privacyRequest.identity],
  );
  const currentRequestId = privacyRequest.id;

  const { data, isFetching } = useSearchPrivacyRequestsQuery(
    {
      identities: identitiesFilter,
      page: 1,
      size: 100,
    },
    { skip: !isOpen || !identitiesFilter },
  );

  const rows = useMemo<RelatedRequestRow[]>(() => {
    const items = (data?.items ?? []) as RelatedRequestRow[];
    // Pin the current request to the top so users always see it in context.
    return [...items].sort((a, b) => {
      if (a.id === currentRequestId) {
        return -1;
      }
      if (b.id === currentRequestId) {
        return 1;
      }
      return 0;
    });
  }, [data, currentRequestId]);

  const columns = useMemo<ColumnsType<RelatedRequestRow>>(
    () => [
      {
        title: "Request ID",
        dataIndex: "id",
        key: "id",
        render: (id: string) =>
          id === currentRequestId ? (
            <Flex gap="small" align="center">
              <Typography.Text>{id}</Typography.Text>
              <Tag color={CUSTOM_TAG_COLOR.INFO}>Current</Tag>
            </Flex>
          ) : (
            <RouterLink
              href={`${PRIVACY_REQUESTS_ROUTE}/${id}`}
              target="_blank"
              rel="noopener noreferrer"
              data-testid="related-requests-drawer-link"
            >
              {id}
            </RouterLink>
          ),
      },
      {
        title: "Created at",
        dataIndex: "created_at",
        key: "created_at",
        render: (value: string | null | undefined) =>
          value ? formatDate(value) : "—",
      },
      {
        title: "Source",
        dataIndex: "source",
        key: "source",
        render: (value: string | null | undefined) => value ?? "—",
      },
      {
        title: "Status",
        dataIndex: "status",
        key: "status",
        render: (status: PrivacyRequestStatus) => {
          const props = statusPropMap[status];
          return props ? (
            <Tag color={props.colorScheme}>{props.label}</Tag>
          ) : (
            <Tag>{status}</Tag>
          );
        },
      },
    ],
    [currentRequestId],
  );

  return (
    <Drawer
      open={isOpen}
      onClose={onClose}
      width="50vw"
      autoFocus={false}
      destroyOnHidden
      title="Related requests"
    >
      <Typography.Paragraph type="secondary" className="!mb-4">
        Requests that share at least one identity value (e.g. email, phone) with
        this one — including any that were marked as duplicates. Use this to see
        the full context across submissions from the same subject.
      </Typography.Paragraph>
      <Table<RelatedRequestRow>
        data-testid="related-requests-drawer-table"
        rowKey="id"
        columns={columns}
        dataSource={rows}
        loading={isFetching}
        pagination={false}
        size="small"
        locale={{ emptyText: "No related requests found." }}
      />
    </Drawer>
  );
};

export default RelatedRequestsDrawer;
