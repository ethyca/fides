/* eslint-disable react/no-unstable-nested-components */
import {
  ColumnDef,
  createColumnHelper,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { Box, Heading, Link, Text } from "fidesui";
import type { NextPage } from "next";
import { useMemo } from "react";

import ClipboardButton from "~/features/common/ClipboardButton";
import Layout from "~/features/common/Layout";
import {
  DefaultCell,
  FidesTableV2,
  TableSkeletonLoader,
} from "~/features/common/table/v2";
import { useGetFidesCloudConfigQuery } from "~/features/plus/plus.slice";

type CNAMERecord = {
  hostName: string;
  type: string;
  data: string;
};

const columnHelper = createColumnHelper<CNAMERecord>();

const DomainRecordsPage: NextPage = () => {
  const columns: ColumnDef<CNAMERecord, any>[] = useMemo(
    () => [
      columnHelper.accessor((row) => row.hostName, {
        header: "Name",
        cell: (props) => <DefaultCell value={props.getValue()} />,
      }),
      columnHelper.accessor((row) => row.type, {
        header: "Type",
        cell: (props) => <DefaultCell value={props.getValue()} />,
      }),
      columnHelper.accessor((row) => row.data, {
        header: "Value",
        cell: (props) => <DefaultCell value={props.getValue()} />,
      }),
      columnHelper.display({
        id: "actions",
        cell: ({ row }) => (
          <ClipboardButton
            copyText={row.original.data}
            variant="outline"
            size="xs"
          />
        ),
        header: "Actions",
        maxSize: 65,
      }),
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

  const tableInstance = useReactTable<CNAMERecord>({
    getCoreRowModel: getCoreRowModel(),
    columns,
    data,
    columnResizeMode: "onChange",
  });

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
          {isLoading ? (
            <Box p={2} borderWidth={1}>
              <TableSkeletonLoader rowHeight={26} numRows={5} />
            </Box>
          ) : (
            <FidesTableV2<CNAMERecord> tableInstance={tableInstance} />
          )}
        </Box>
      </Box>
    </Layout>
  );
};
export default DomainRecordsPage;
