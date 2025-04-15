import { createColumnHelper } from "@tanstack/react-table";
import { useMemo } from "react";

import QuestionTooltip from "~/features/common/QuestionTooltip";
import { DefaultCell, DefaultHeaderCell } from "~/features/common/table/v2";
import { TCFRestrictionType, TCFVendorRestriction } from "~/types/api";

import {
  RESTRICTION_TYPE_LABELS,
  VENDOR_RESTRICTION_LABELS,
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
          const value = getValue() as TCFRestrictionType;
          return <DefaultCell value={RESTRICTION_TYPE_LABELS[value]} />;
        },
        header: (props) => (
          <DefaultHeaderCell value="Restriction type" {...props} />
        ),
      }),
      columnHelper.accessor((row) => row.vendor_restriction, {
        id: "vendor_restriction",
        cell: ({ getValue }) => {
          const value = getValue() as TCFVendorRestriction;
          return <DefaultCell value={VENDOR_RESTRICTION_LABELS[value]} />;
        },
        header: (props) => (
          <DefaultHeaderCell value="Vendor restriction" {...props} />
        ),
      }),
      columnHelper.accessor((row) => row.vendor_ids, {
        id: "vendor_ids",
        cell: ({ getValue }) => (
          <DefaultCell value={getValue().join(", ") || "All vendors"} />
        ),
        header: (props) => (
          <DefaultHeaderCell
            value={
              <>
                Vendors{" "}
                <QuestionTooltip label="Specify which vendors the restriction applies to. You can apply restrictions to all vendors, specific vendors by their IDs, or allow only certain vendors while restricting the rest." />
              </>
            }
            {...props}
          />
        ),
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
