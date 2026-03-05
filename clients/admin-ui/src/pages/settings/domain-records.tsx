/* eslint-disable react/no-unstable-nested-components */
import { ColumnsType, Flex, Table, Typography } from "fidesui";
import type { NextPage } from "next";
import { useMemo } from "react";

import ClipboardButton from "~/features/common/ClipboardButton";
import Layout from "~/features/common/Layout";
import { useAntTable, useTableState } from "~/features/common/table/hooks";
import { useGetFidesCloudConfigQuery } from "~/features/plus/plus.slice";

type CNAMERecord = {
  hostName: string;
  type: string;
  data: string;
};

const DomainRecordsPage: NextPage = () => {
  const columns: ColumnsType<CNAMERecord> = useMemo(
    () => [
      {
        title: "Name",
        dataIndex: "hostName",
        key: "hostName",
      },
      {
        title: "Type",
        dataIndex: "type",
        key: "type",
      },
      {
        title: "Value",
        dataIndex: "data",
        key: "data",
      },
      {
        title: "Actions",
        dataIndex: "actions",
        key: "actions",
        render: (_, { data }) => (
          <ClipboardButton copyText={data} type="default" size="small" />
        ),
      },
    ],
    [],
  );

  const { data: fidesCloudConfig, isLoading } = useGetFidesCloudConfigQuery();

  const data = useMemo<CNAMERecord[]>(
    () =>
      fidesCloudConfig?.domain_verification_records
        ? fidesCloudConfig.domain_verification_records.map((dr) => ({
            hostName: "www",
            type: "CNAME",
            data: dr,
          }))
        : [],
    [fidesCloudConfig],
  );

  const tableState = useTableState();

  const { tableProps } = useAntTable(tableState, {
    dataSource: data,
    totalRows: data.length,
    isLoading,
  });

  return (
    <Layout title="Domain records">
      <Flex vertical gap="small" data-testid="domain-records">
        <Typography.Title level={2}>Domain records</Typography.Title>
        <Flex vertical>
          <Typography.Paragraph>
            Set the following record on your DNS provider to continue.
          </Typography.Paragraph>
          <Typography.Paragraph>
            Please visit{" "}
            <Typography.Link
              color="complimentary.500"
              href="https://fid.es/manage-dns"
              target="_blank"
            >
              docs.ethyca.com
            </Typography.Link>{" "}
            for more information on how to configure Domain records.
          </Typography.Paragraph>
          <Table
            {...tableProps}
            columns={columns}
            data-testid="domain-records-table"
          />
        </Flex>
      </Flex>
    </Layout>
  );
};
export default DomainRecordsPage;
