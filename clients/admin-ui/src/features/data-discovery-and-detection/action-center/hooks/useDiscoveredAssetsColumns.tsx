import { ColumnDef, createColumnHelper } from "@tanstack/react-table";

import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import {
  DefaultCell,
  IndeterminateCheckboxCell,
} from "~/features/common/table/v2";
import {
  BadgeCellExpandable,
  DefaultHeaderCell,
  ListCellExpandable,
} from "~/features/common/table/v2/cells";
import { DiscoveredAssetActionsCell } from "~/features/data-discovery-and-detection/action-center/tables/cells/DiscoveredAssetActionsCell";
import DiscoveredAssetDataUseCell from "~/features/data-discovery-and-detection/action-center/tables/cells/DiscoveredAssetDataUseCell";
import { PrivacyNoticeRegion, StagedResourceAPIResponse } from "~/types/api";

import { SystemCell } from "../tables/cells/SystemCell";

export const useDiscoveredAssetsColumns = ({
  readonly,
}: {
  readonly: boolean;
}) => {
  const columnHelper = createColumnHelper<StagedResourceAPIResponse>();

  const readonlyColumns: ColumnDef<StagedResourceAPIResponse, any>[] = [
    columnHelper.accessor((row) => row.name, {
      id: "name",
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: "Asset",
      size: 300,
    }),
    columnHelper.accessor((row) => row.resource_type, {
      id: "resource_type",
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: "Type",
    }),
    columnHelper.accessor((row) => row.system, {
      id: "system",
      cell: (props) =>
        !!props.row.original.monitor_config_id && (
          <SystemCell
            aggregateSystem={props.row.original}
            monitorConfigId={props.row.original.monitor_config_id}
            readonly={readonly}
          />
        ),
      header: "System",
      size: 200,
      meta: {
        noPadding: true,
      },
    }),
    columnHelper.display({
      id: "data_use",
      cell: (props) => (
        <DiscoveredAssetDataUseCell
          asset={props.row.original}
          readonly={readonly}
        />
      ),
      header: "Categories of consent",
      size: 400,
      meta: {
        disableRowClick: true,
      },
    }),
    columnHelper.accessor((row) => row.locations, {
      id: "locations",
      cell: (props) => (
        <BadgeCellExpandable
          values={props.getValue().map((location: PrivacyNoticeRegion) => ({
            label: PRIVACY_NOTICE_REGION_RECORD[location],
            key: location,
          }))}
          cellProps={props as any}
        />
      ),
      header: "Locations",
      size: 300,
      meta: {
        showHeaderMenu: true,
        disableRowClick: true,
      },
    }),
    columnHelper.accessor((row) => row.domain, {
      id: "domain",
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: "Domain",
    }),
    /*
    // TODO: [HJ-344] uncomment when monitor supports discovery status
    columnHelper.accessor((row) => row.with_consent, {
      id: "with_consent",
      cell: (props) => (
        <DiscoveryStatusBadgeCell
          withConsent={props.getValue()}
          dateDiscovered={props.row.original.updated_at}
        />
      ),
      header: "Discovery",
    }), */
    columnHelper.accessor((row) => row.page, {
      id: "page",
      cell: (props) => (
        <ListCellExpandable
          values={props.getValue()}
          valueSuffix="pages"
          cellProps={props}
        />
      ),
      header: (props) => <DefaultHeaderCell value="Detected on" {...props} />,
      meta: {
        showHeaderMenu: true,
        disableRowClick: true,
      },
    }),
  ];

  if (readonly) {
    return { columns: readonlyColumns };
  }

  const editableColumns = [
    columnHelper.display({
      id: "select",
      cell: ({ row }) => (
        <IndeterminateCheckboxCell
          isChecked={row.getIsSelected()}
          onChange={row.getToggleSelectedHandler()}
          dataTestId={`select-${row.original.name || row.id}`}
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
      maxSize: 40,
    }),
    ...readonlyColumns,
    columnHelper.display({
      id: "actions",
      cell: (props) => (
        <DiscoveredAssetActionsCell asset={props.row.original} />
      ),
      header: "Actions",
      meta: {
        disableRowClick: true,
      },
    }),
  ];

  return { columns: editableColumns };
};
