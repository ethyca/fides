import { ColumnDef, createColumnHelper } from "@tanstack/react-table";

import { DefaultCell, DefaultHeaderCell } from "~/features/common/table/v2";
import { RelativeTimestampCell } from "~/features/common/table/v2/cells";
import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";
import { StagedResourceType } from "~/features/data-discovery-and-detection/types/StagedResourceType";

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
      columnHelper.accessor((row) => row.name, {
        id: "tables",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Table name" {...props} />,
      }),
      columnHelper.display({
        id: "type",
        cell: () => <DefaultCell value="Table" />,
        header: "Type",
      }),
      columnHelper.accessor((row) => row.modified, {
        id: "time",
        cell: (props) => <RelativeTimestampCell time={props.getValue()} />,
        header: "Time",
      }),
      columnHelper.display({
        id: "actions",
        cell: () => <DefaultCell value="actions (placeholder)" />,
        header: "Actions",
      }),
    ];
    return { columns };
  }

  if (resourceType === StagedResourceType.FIELD) {
    const columns = [
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: (props) => <DefaultCell value={props.getValue()} />,
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
            />
          );
        },
        header: "Data category",
        minSize: 240, // keep a minimum width so the Select has space to display the options properly
      }),
      columnHelper.accessor((row) => row.modified, {
        id: "time",
        cell: (props) => <RelativeTimestampCell time={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="When" {...props} />,
      }),
    ];
    return { columns };
  }

  return { columns: defaultColumns };
};

export default useDiscoveryResultColumns;
