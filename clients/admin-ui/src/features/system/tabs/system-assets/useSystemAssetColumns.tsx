import { ColumnDef, createColumnHelper } from "@tanstack/react-table";

import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import { DefaultCell } from "~/features/common/table/v2";
import {
  BadgeCellExpandable,
  DefaultHeaderCell,
  ListCellExpandable,
} from "~/features/common/table/v2/cells";
import SystemAssetsDataUseCell from "~/features/system/tabs/system-assets/SystemAssetsDataUseCell";
import { Asset, PrivacyNoticeRegion } from "~/types/api";

const useSystemAssetColumns = () => {
  const columnHelper = createColumnHelper<Asset>();

  const columns: ColumnDef<Asset, any>[] = [
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
    columnHelper.accessor((row) => row.data_uses, {
      id: "data_uses",
      cell: (props) => <SystemAssetsDataUseCell values={props.getValue()} />,
      header: "Categories of consent",
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
      meta: {
        width: "auto",
      },
    }),
    columnHelper.accessor((row) => row.domain, {
      id: "domain",
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: "Domain",
    }),
    // @ts-ignore - un-ignore when API "Asset" type is updated with "page" field (HA-504)
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

  return columns;
};

export default useSystemAssetColumns;
