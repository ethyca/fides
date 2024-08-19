import { createColumnHelper } from "@tanstack/react-table";

import { DefaultCell, DefaultHeaderCell } from "~/features/common/table/v2";
import { formatDate, getPII } from "~/features/common/utils";
import {
  RequestActionTypeCell,
  RequestDaysLeftCell,
  RequestStatusBadgeCell,
} from "~/features/privacy-requests/cells";
import { RequestTableActions } from "~/features/privacy-requests/RequestTableActions";
import { PrivacyRequestEntity } from "~/features/privacy-requests/types";

// eslint-disable-next-line @typescript-eslint/naming-convention
enum COLUMN_IDS {
  STATUS = "status",
  DAYS_LEFT = "due_date",
  REQUEST_TYPE = "request_type",
  SUBJECT_IDENTITY = "subject_identity",
  TIME_RECIEVED = "created_at",
  CREATED_BY = "created_by",
  REVIEWER = "reviewer",
  ID = "id",
  ACTIONS = "actions",
}

const columnHelper = createColumnHelper<PrivacyRequestEntity>();

export const getRequestTableColumns = (revealPII = false) => [
  columnHelper.accessor((row) => row.status, {
    id: COLUMN_IDS.STATUS,
    cell: ({ getValue }) => <RequestStatusBadgeCell value={getValue()} />,
    header: (props) => <DefaultHeaderCell value="Status" {...props} />,
  }),
  columnHelper.accessor((row) => row.days_left, {
    id: COLUMN_IDS.DAYS_LEFT,
    cell: ({ row, getValue }) => (
      <RequestDaysLeftCell
        daysLeft={getValue()}
        timeframe={row.original.policy.execution_timeframe}
        status={row.original.status}
      />
    ),
    header: (props) => <DefaultHeaderCell value="Days left" {...props} />,
  }),
  columnHelper.accessor((row) => row.policy.rules, {
    id: COLUMN_IDS.REQUEST_TYPE,
    cell: ({ getValue }) => <RequestActionTypeCell value={getValue()} />,
    header: (props) => <DefaultHeaderCell value="Request type" {...props} />,
    enableSorting: false,
  }),
  columnHelper.accessor(
    (row) =>
      row.identity?.email.value || row.identity?.phone_number.value || "",
    {
      id: COLUMN_IDS.SUBJECT_IDENTITY,
      cell: ({ getValue }) => (
        <DefaultCell value={getPII(getValue(), revealPII)} />
      ),
      header: (props) => (
        <DefaultHeaderCell value="Subject identity" {...props} />
      ),
      enableSorting: false,
    },
  ),
  columnHelper.accessor((row) => row.created_at, {
    id: COLUMN_IDS.TIME_RECIEVED,
    cell: ({ getValue }) => <DefaultCell value={formatDate(getValue())} />,
    header: (props) => <DefaultHeaderCell value="Time received" {...props} />,
  }),
  columnHelper.accessor((row) => row.reviewer?.username || "", {
    id: COLUMN_IDS.REVIEWER,
    cell: ({ getValue }) => (
      <DefaultCell value={getPII(getValue(), revealPII)} /> // NOTE: this field does not get set when reviewed as root user
    ),
    header: (props) => <DefaultHeaderCell value="Reviewed by" {...props} />,
    enableSorting: false,
  }),
  columnHelper.accessor((row) => row.id, {
    id: COLUMN_IDS.ID,
    cell: ({ getValue }) => <DefaultCell value={getValue()} />,
    header: (props) => <DefaultHeaderCell value="Request ID" {...props} />,
    enableSorting: false,
  }),
  columnHelper.display({
    id: COLUMN_IDS.ACTIONS,
    cell: ({ row }) => <RequestTableActions subjectRequest={row.original} />,
    header: (props) => <DefaultHeaderCell value="Actions" {...props} />,
    meta: {
      disableRowClick: true,
    },
  }),
];
