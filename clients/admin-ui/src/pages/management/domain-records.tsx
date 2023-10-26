import { Box, Heading, Link, Text } from "@fidesui/react";
import type { NextPage } from "next";
import { useMemo } from "react";
import { Column } from "react-table";

import Layout from "~/features/common/Layout";
import { FidesTable, WrappedCell } from "~/features/common/table";
import { ClipboardCell } from "~/features/common/table/cells";
import { FidesObject } from "~/features/common/table/FidesTable";
import { useGetFidesCloudConfigQuery } from "~/features/plus/plus.slice";

type CNAMERecord = {
  hostName: string;
  type: string;
  data: string;
} & FidesObject;

const DomainRecordsPage: NextPage = () => {
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
    [fidesCloudConfig]
  );

  if (isLoading) {
    return <div>loading</div>;
  }

  return (
    <Layout title="Domain records">
      <Box data-testid="domain-records">
        <Heading marginBottom={4} fontSize="2xl">
          Domain records
        </Heading>
        <Box maxWidth="600px">
          <Text marginBottom={2} fontSize="md">
            Set the following record on your DNS provider to continue.
          </Text>
          <Text mb={10} fontSize="sm">
            Please visit{" "}
            <Link
              color="complimentary.500"
              href="https://fid.es/manage-dns"
              isExternal
            >
              docs.ethyca.com
            </Link>{" "}
            for more information on how to configure Domain records.
          </Text>
          <FidesTable<CNAMERecord> columns={columns} data={data} />
        </Box>
      </Box>
    </Layout>
  );
};
export default DomainRecordsPage;
