import { useMemo } from "react";
import {
  createColumnHelper,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";

import { useFeatures } from "common/features";

import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  GlobalFilterV2,
  IndeterminateCheckboxCell,
  PAGE_SIZES,
  PaginationBar,
  RowSelectionBar,
  TableActionBar,
  TableSkeletonLoader,
} from "common/table/v2";

type TcfConsentMangagement = {
  id: string;
  name: string;
  data_uses: number;
  legal_bases: number;
};

const columnHelper = createColumnHelper<TcfConsentMangagement>();

import { useGetVendorReportQuery } from "~/features/plus/plus.slice";

export const ConsentManagementTable = () => {
  const { data: report } = useGetVendorReportQuery();
  console.log(report);

  const tcfColumns = useMemo(
    () => [
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultCell value="Vendor" {...props} />,
      }),
      columnHelper.accessor((row) => row.data_uses, {
        id: "Data Uses",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultCell value="Data Uses" {...props} />,
      }),
      columnHelper.accessor((row) => row.legal_bases, {
        id: "legal_bases",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultCell value="legal_bases" {...props} />,
      }),
    ],
    []
  );

  const tableInstance = useReactTable<TcfConsentMangagement>({
    columns: tcfColumns,
    data: report.items,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div>
      <FidesTableV2 tableInstance={tableInstance} />
    </div>
  );
};
