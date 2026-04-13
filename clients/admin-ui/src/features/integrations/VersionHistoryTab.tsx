import { formatDate } from "common/utils";
import {
  Button,
  CUSTOM_TAG_COLOR,
  Spin,
  Table,
  Tag,
  Typography,
} from "fidesui";
import React, { useMemo, useState } from "react";

import { useGetConnectorTemplateVersionsQuery } from "~/features/connector-templates/connector-template.slice";
import SaaSVersionModal from "~/features/connector-templates/SaaSVersionModal";
import { SaaSConfigVersionResponse } from "~/types/api";

interface VersionHistoryTabProps {
  connectorType: string;
}

const VersionHistoryTab = ({ connectorType }: VersionHistoryTabProps) => {
  const {
    data: versions,
    isLoading,
    isError,
  } = useGetConnectorTemplateVersionsQuery(connectorType);

  const [selected, setSelected] = useState<SaaSConfigVersionResponse | null>(
    null,
  );

  const columns = useMemo(
    () => [
      {
        title: "Version",
        dataIndex: "version",
        key: "version",
        render: (v: string) => <Typography.Text>v{v}</Typography.Text>,
      },
      {
        title: "Type",
        dataIndex: "is_custom",
        key: "is_custom",
        render: (isCustom: boolean) => (
          <Tag
            color={
              isCustom ? CUSTOM_TAG_COLOR.WARNING : CUSTOM_TAG_COLOR.DEFAULT
            }
          >
            {isCustom ? "Custom" : "OOB"}
          </Tag>
        ),
      },
      {
        title: "Captured at",
        dataIndex: "created_at",
        key: "created_at",
        render: (ts: string) => (
          <Typography.Text type="secondary">{formatDate(ts)}</Typography.Text>
        ),
      },
      {
        title: "",
        key: "actions",
        render: (_: unknown, row: SaaSConfigVersionResponse) => (
          <Button size="small" onClick={() => setSelected(row)}>
            View
          </Button>
        ),
      },
    ],
    [setSelected],
  );

  if (isLoading) {
    return <Spin />;
  }

  if (isError) {
    return (
      <Typography.Text type="danger">
        Could not load version history.
      </Typography.Text>
    );
  }

  if (!versions || versions.length === 0) {
    return (
      <Typography.Text type="secondary">
        No version history captured yet.
      </Typography.Text>
    );
  }

  return (
    <>
      <Typography.Paragraph className="mb-4 max-w-3xl">
        All captured versions of this connector&apos;s configuration. Each entry
        reflects the config and dataset snapshot at the time it was recorded.
      </Typography.Paragraph>
      <Table
        dataSource={versions}
        columns={columns}
        rowKey={(row: SaaSConfigVersionResponse) =>
          `${row.connector_type}-${row.version}-${row.created_at}`
        }
        size="small"
        pagination={false}
      />
      {selected && (
        <SaaSVersionModal
          isOpen
          onClose={() => setSelected(null)}
          connectorType={selected.connector_type}
          version={selected.version}
        />
      )}
    </>
  );
};

export default VersionHistoryTab;
