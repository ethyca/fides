import { ColumnDef, createColumnHelper } from "@tanstack/react-table";

import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import { DefaultCell } from "~/features/common/table/v2";
import { BadgeCellExpandable } from "~/features/common/table/v2/cells";
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
    columnHelper.accessor((row) => row.parent, {
      id: "parent",
      cell: (props) => (
        <BadgeCellExpandable
          values={props.getValue().map((parent: string) => ({
            label: parent,
            key: parent,
          }))}
        />
      ),
      header: "Parent",
      meta: {
        width: "auto",
      },
    }),
  ];

  return columns;
};

export default useSystemAssetColumns;
