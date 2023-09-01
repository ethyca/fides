import { Box, Heading, Link, Text } from "@fidesui/react";
import type { NextPage } from "next";
import { useMemo } from "react";
import { Column } from "react-table";

import Layout from "~/features/common/Layout";
import { FidesTable, WrappedCell } from "~/features/common/table";
import { ClipboardCell } from "~/features/common/table/cells";
import EmptyTableState from "~/features/common/table/EmptyTableState";
import { FidesObject } from "~/features/common/table/FidesTable";

type CNAMERecord = {
  hostName: string;
  type: string;
  data: string;
} & FidesObject;

const DNSRecordsPage: NextPage = () => {
  const columns: Column<CNAMERecord>[] = useMemo(
    () => [
      {
        Header: "Name",
        accessor: "hostName",
        Cell: WrappedCell,
      },
      {
        Header: "Type",
        accessor: "type",
        Cell: WrappedCell,
      },
      {
        Header: "Value",
        accessor: "data",
        Cell: ClipboardCell,
      },
    ],
    []
  );

  const data = useMemo<CNAMERecord[]>(
    () => [
      {
        hostName: "www",
        type: "CNAME",
        data: "cname.ethyca-dns.com",
      },
    ],
    []
  );

  return (
    <Layout title="DNS Records">
      <Box data-testid="dns-records">
        <Heading marginBottom={4} fontSize="2xl">
          DNS Records
        </Heading>
        <Box maxWidth="600px">
          <Box mt={4} mb={4}>
            <EmptyTableState
              title="Configuration not validated"
              description="Depending on your provider, it might take some time for the DNS records to apply"
            />
          </Box>
          <Text marginBottom={2} fontSize="md">
            Set the follow record on your DNS provider to continue.
          </Text>
          <Text mb={10} fontSize="sm">
            Please visit{" "}
            <Link
              color="complimentary.500"
              href="https://docs.ethyca.com"
              isExternal
            >
              docs.ethyca.com
            </Link>{" "}
            for more information on how to configure DNS records.
          </Text>
          <FidesTable<CNAMERecord> columns={columns} data={data} />
        </Box>
      </Box>
    </Layout>
  );
};
export default DNSRecordsPage;
