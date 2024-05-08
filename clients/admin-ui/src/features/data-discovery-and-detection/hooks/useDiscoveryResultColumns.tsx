import { ColumnDef, createColumnHelper } from "@tanstack/react-table";

import { DefaultCell, DefaultHeaderCell } from "~/features/common/table/v2";
import {
  IndeterminateCheckboxCell,
  RelativeTimestampCell,
} from "~/features/common/table/v2/cells";
import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";
import { StagedResourceType } from "~/features/data-discovery-and-detection/types/StagedResourceType";

import DiscoveryItemActions from "../DiscoveryItemActions";
import ResultStatusCell from "../tables/ResultStatusCell";
import TaxonomyDisplayAndEdit from "../TaxonomyDisplayAndEdit";

const useDiscoveryResultColumns = ({
  resourceType,
}: {
  resourceType: StagedResourceType | undefined;
}) => {
  const columnHelper = createColumnHelper<DiscoveryMonitorItem>();

  const defaultColumns: ColumnDef<DiscoveryMonitorItem, any>[] = [];

  if (!resourceType) {
    return { columns: defaultColumns };
  }

  if (resourceType === StagedResourceType.TABLE) {
    const columns = [
      columnHelper.display({
        id: "select",
        cell: ({ row }) => (
          <IndeterminateCheckboxCell
            isChecked={row.getIsSelected()}
            onChange={row.getToggleSelectedHandler()}
            dataTestId={`select-${row.original.name ?? row.id}`}
          />
        ),
        header: ({ table }) => (
          <IndeterminateCheckboxCell
            isChecked={table.getIsAllPageRowsSelected()}
            isIndeterminate={table.getIsSomeRowsSelected()}
            onChange={table.getToggleAllRowsSelectedHandler()}
            dataTestId="select-all-rows"
          />
        ),
        maxSize: 25,
      }),
      columnHelper.accessor((row) => row.name, {
        id: "tables",
        cell: (props) => <ResultStatusCell result={props.row.original} />,
        header: (props) => <DefaultHeaderCell value="Table name" {...props} />,
      }),
      columnHelper.display({
        id: "type",
        cell: () => <DefaultCell value="Table" />,
        header: "Type",
      }),
      columnHelper.accessor((row) => row.source_modified, {
        id: "time",
        cell: (props) => <RelativeTimestampCell time={props.getValue()} />,
        header: "Time",
      }),
      columnHelper.display({
        id: "actions",
        cell: (props) => <DiscoveryItemActions resource={props.row.original} />,
        header: "Actions",
      }),
    ];
    return { columns };
  }

  if (resourceType === StagedResourceType.FIELD) {
    const columns = [
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: (props) => <ResultStatusCell result={props.row.original} />,
        header: (props) => <DefaultHeaderCell value="Field name" {...props} />,
      }),
      columnHelper.display({
        id: "type",
        cell: () => <DefaultCell value="Field" />,
        header: "Type",
      }),
      columnHelper.accessor((row) => row.classifications, {
        id: "classifications",
        cell: (props) => {
          const bestTaxonomyMatch = props.getValue()?.length
            ? props.getValue()![0]
            : null;

          return (
            <TaxonomyDisplayAndEdit
              fidesLangKey={bestTaxonomyMatch?.label}
              isEditable
              resource={props.row.original}
            />
          );
        },
        meta: { overflow: "visible" },
        header: "Data category",
        minSize: 280, // keep a minimum width so the Select has space to display the options properly
      }),
      columnHelper.accessor((row) => row.source_modified, {
        id: "time",
        cell: (props) => <RelativeTimestampCell time={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="When" {...props} />,
      }),
      columnHelper.display({
        id: "actions",
        cell: (props) => <DiscoveryItemActions resource={props.row.original} />,
        header: "Actions",
      }),
    ];
    return { columns };
  }

  return { columns: defaultColumns };
};

export default useDiscoveryResultColumns;
