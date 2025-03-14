import { ColumnDef, createColumnHelper } from "@tanstack/react-table";

import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import { DefaultCell } from "~/features/common/table/v2";
import {
  BadgeCellExpandable,
  DefaultHeaderCell,
  ListCellExpandable,
} from "~/features/common/table/v2/cells";
import SystemAssetsDataUseCell from "~/features/system/tabs/system-assets/SystemAssetsDataUseCell";
import { PrivacyNoticeRegion } from "~/types/api";
import { StagedResourceAPIResponse } from "~/types/api/models/StagedResourceAPIResponse";

const useSystemAssetColumns = () => {
  const columnHelper = createColumnHelper<StagedResourceAPIResponse>();

  const columns: ColumnDef<StagedResourceAPIResponse, any>[] = [
    columnHelper.accessor((row) => row.name, {
      id: "name",
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: "Asset",
    }),
    columnHelper.accessor((row) => row.resource_type, {
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
