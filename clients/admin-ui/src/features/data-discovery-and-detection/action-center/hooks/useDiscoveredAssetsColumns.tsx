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
import {
  AggregatedConsent,
  PrivacyNoticeRegion,
  StagedResourceAPIResponse,
} from "~/types/api";

import { DiscoveryStatusBadgeCell } from "../tables/cells/DiscoveryStatusBadgeCell";
import { SystemCell } from "../tables/cells/SystemCell";
import { ActionCenterTabHash } from "./useActionCenterTabs";

export const useDiscoveredAssetsColumns = ({
  readonly,
  onTabChange,
}: {
  readonly: boolean;
  onTabChange: (tab: ActionCenterTabHash) => void;
}) => {
  const columnHelper = createColumnHelper<StagedResourceAPIResponse>();

  const readonlyColumns: ColumnDef<StagedResourceAPIResponse, any>[] = [
    columnHelper.accessor((row) => row.name, {
      id: "name",
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: "Asset",
      size: 300,
      meta: {
        headerProps: readonly
          ? undefined
          : {
              paddingLeft: "0px",
            },
        cellProps: readonly
          ? undefined
          : {
              padding: "0 !important",
            },
      },
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
            label: PRIVACY_NOTICE_REGION_RECORD[location] ?? location,
            key: location,
          }))}
          cellProps={props}
        />
      ),
      header: (props) => <DefaultHeaderCell value="Locations" {...props} />,
      size: 300,
      meta: {
        showHeaderMenu: true,
        disableRowClick: true,
      },
    }),
    columnHelper.accessor((row) => row.domain, {
      id: "domain",
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => <DefaultHeaderCell value="Domain" {...props} />,
    }),
    columnHelper.accessor((row) => row.consent_aggregated, {
      id: "consent_aggregated",
      cell: (props) => (
        <DiscoveryStatusBadgeCell
          consentAggregated={props.getValue() ?? AggregatedConsent.UNKNOWN}
          stagedResource={props.row.original}
        />
      ),
      header: "Discovery",
    }),
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
      meta: {
        cellProps: {
          borderRight: "none",
        },
      },
    }),
    ...readonlyColumns,
    columnHelper.display({
      id: "actions",
      cell: (props) => (
        <DiscoveredAssetActionsCell
          asset={props.row.original}
          onTabChange={onTabChange}
        />
      ),
      header: "Actions",
      meta: {
        disableRowClick: true,
      },
    }),
  ];

  return { columns: editableColumns };
};
