import { ColumnDef, createColumnHelper } from "@tanstack/react-table";
import { AntTag } from "fidesui";

import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import { DefaultCell } from "~/features/common/table/v2";
import {
  BadgeCellExpandable,
  DefaultHeaderCell,
  IndeterminateCheckboxCell,
  ListCellExpandable,
} from "~/features/common/table/v2/cells";
import SystemAssetActionsCell from "~/features/system/tabs/system-assets/SystemAssetActionsCell";
import SystemAssetsDataUseCell from "~/features/system/tabs/system-assets/SystemAssetsDataUseCell";
import { Asset, PrivacyNoticeRegion } from "~/types/api";

const useSystemAssetColumns = ({
  systemKey,
  systemName,
  onEditClick,
}: {
  systemKey: string;
  systemName: string;
  onEditClick: (asset: Asset) => void;
}) => {
  const columnHelper = createColumnHelper<Asset>();

  const columns: ColumnDef<Asset, any>[] = [
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
          paddingRight: 0,
        },
      },
    }),
    columnHelper.accessor((row) => row.name, {
      id: "name",
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: "Asset",
    }),
    columnHelper.accessor((row) => row.asset_type, {
      id: "resource_type",
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: "Type",
    }),
    columnHelper.display({
      id: "system",
      cell: () => <AntTag color="white">{systemName}</AntTag>,
      header: "System",
    }),
    columnHelper.accessor((row) => row.data_uses, {
      id: "data_uses",
      cell: (props) => (
        <SystemAssetsDataUseCell
          asset={props.row.original}
          systemId={systemKey}
        />
      ),
      header: "Categories of consent",
      size: 200,
    }),
    columnHelper.accessor((row) => row.locations, {
      id: "locations",
      cell: (props) => (
        <BadgeCellExpandable
          values={props.getValue().map((location: PrivacyNoticeRegion) => ({
            label: PRIVACY_NOTICE_REGION_RECORD[location],
            key: location,
          }))}
        />
      ),
      header: "Locations",
      size: 300,
    }),
    columnHelper.accessor((row) => row.domain, {
      id: "domain",
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: "Domain",
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
    columnHelper.display({
      id: "actions",
      cell: ({ row }) => (
        <SystemAssetActionsCell
          asset={row.original}
          systemKey={systemKey}
          onEditClick={() => onEditClick(row.original)}
        />
      ),
      header: "Actions",
    }),
  ];

  return columns;
};

export default useSystemAssetColumns;
