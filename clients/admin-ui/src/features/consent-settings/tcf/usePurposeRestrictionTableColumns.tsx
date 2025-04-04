import { createColumnHelper } from "@tanstack/react-table";
import { useMemo } from "react";

import { DefaultCell, DefaultHeaderCell } from "~/features/common/table/v2";

import {
  RESTRICTION_TYPE_LABELS,
  RestrictionType,
  VENDOR_RESTRICTION_LABELS,
  VendorRestriction,
} from "./constants";
import { PublisherRestrictionActionCell } from "./PublisherRestrictionActionCell";
import { PurposeRestriction } from "./types";

const columnHelper = createColumnHelper<PurposeRestriction>();

export const usePurposeRestrictionTableColumns = () => {
  const columns = useMemo(
    () => [
      columnHelper.accessor((row) => row.restriction_type, {
        id: "restriction_type",
        cell: ({ getValue }) => {
          const value = getValue() as RestrictionType;
          return <DefaultCell value={RESTRICTION_TYPE_LABELS[value]} />;
        },
        header: (props) => (
          <DefaultHeaderCell value="Restriction Type" {...props} />
        ),
      }),
      columnHelper.accessor((row) => row.vendor_restriction, {
        id: "vendor_restriction",
        cell: ({ getValue }) => {
          const value = getValue() as VendorRestriction;
          return <DefaultCell value={VENDOR_RESTRICTION_LABELS[value]} />;
        },
        header: (props) => (
          <DefaultHeaderCell value="Vendor Restriction" {...props} />
        ),
      }),
      columnHelper.accessor((row) => row.vendor_ids, {
        id: "vendor_ids",
        cell: ({ getValue }) => <DefaultCell value={getValue().join(", ")} />,
        header: (props) => <DefaultHeaderCell value="Vendor IDs" {...props} />,
      }),
      columnHelper.display({
        id: "actions",
        cell: (props) => (
          <PublisherRestrictionActionCell
            currentValues={props.row.original}
            existingRestrictions={props.table
              .getRowModel()
              .rows.map((row) => row.original)}
          />
        ),
        header: "Actions",
        size: 154,
        meta: {
          disableRowClick: true,
        },
      }),
    ],
    [],
  );

  return columns;
};
