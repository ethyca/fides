import React, { useState } from "react";

import { formatDate } from "common/utils";
import {
  Button,
  ChakraSpinner as Spinner,
  ChakraText as Text,
  CUSTOM_TAG_COLOR,
  Table,
  Tag,
  Typography,
} from "fidesui";

import SaaSVersionModal from "~/features/connector-templates/SaaSVersionModal";
import {
  SaaSConfigVersionResponse,
  useGetConnectorTemplateVersionsQuery,
} from "~/features/connector-templates/connector-template.slice";

interface VersionHistoryTabProps {
  connectorType: string;
}

const VersionHistoryTab = ({ connectorType }: VersionHistoryTabProps) => {
  const { data: versions, isLoading } =
    useGetConnectorTemplateVersionsQuery(connectorType);

  const [selected, setSelected] = useState<SaaSConfigVersionResponse | null>(
    null,
  );

  const columns = [
    {
      title: "Version",
      dataIndex: "version",
      key: "version",
      render: (v: string) => (
        <Text fontSize="sm" fontWeight="medium">
          v{v}
        </Text>
      ),
    },
    {
      title: "Type",
      dataIndex: "is_custom",
      key: "is_custom",
      render: (isCustom: boolean) => (
        <Tag color={isCustom ? CUSTOM_TAG_COLOR.WARNING : CUSTOM_TAG_COLOR.DEFAULT}>
          {isCustom ? "Custom" : "OOB"}
        </Tag>
      ),
    },
    {
      title: "Captured at",
      dataIndex: "created_at",
      key: "created_at",
      render: (ts: string) => (
        <Text fontSize="sm" color="gray.600">
          {formatDate(ts)}
        </Text>
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
  ];

  if (isLoading) {
    return <Spinner />;
  }

  if (!versions || versions.length === 0) {
    return (
      <Text color="gray.500" fontSize="sm">
        No version history captured yet.
      </Text>
    );
  }

  return (
    <>
      <Typography.Paragraph className="mb-4 max-w-3xl">
        All captured versions of this connector&apos;s configuration. Each
        entry reflects the config and dataset snapshot at the time it was
        recorded.
      </Typography.Paragraph>
      <Table
        dataSource={versions}
        columns={columns}
        rowKey={(row: SaaSConfigVersionResponse) =>
          `${row.version}-${row.is_custom}-${row.created_at}`
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
