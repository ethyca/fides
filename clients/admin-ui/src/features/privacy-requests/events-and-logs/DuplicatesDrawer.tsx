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
import { PrivacyRequestStatus } from "~/types/api";

type DuplicateRequestRow = {
  id: string;
  status: PrivacyRequestStatus;
  created_at?: string | null;
  source?: string | null;
};

type DuplicatesDrawerProps = {
  isOpen: boolean;
  onClose: () => void;
  duplicateRequestGroupId: string;
  currentRequestId: string;
};

const DuplicatesDrawer = ({
  isOpen,
  onClose,
  duplicateRequestGroupId,
  currentRequestId,
}: DuplicatesDrawerProps) => {
  const { data, isFetching } = useSearchPrivacyRequestsQuery(
    {
      duplicate_request_group_id: duplicateRequestGroupId,
      page: 1,
      size: 100,
    },
    { skip: !isOpen || !duplicateRequestGroupId },
  );

  const rows = useMemo<DuplicateRequestRow[]>(() => {
    const items = (data?.items ?? []) as DuplicateRequestRow[];
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

  const columns = useMemo<ColumnsType<DuplicateRequestRow>>(
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
              data-testid="duplicates-drawer-link"
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
      title="Duplicate requests"
    >
      <Table<DuplicateRequestRow>
        data-testid="duplicates-drawer-table"
        rowKey="id"
        columns={columns}
        dataSource={rows}
        loading={isFetching}
        pagination={false}
        size="small"
        locale={{ emptyText: "No duplicate requests found." }}
      />
    </Drawer>
  );
};

export default DuplicatesDrawer;
