import { createColumnHelper } from "@tanstack/react-table";
import { formatIsoLocation, isoStringToEntry } from "fidesui";

import {
  BadgeCell,
  DefaultCell,
  DefaultHeaderCell,
} from "~/features/common/table/v2";
import { formatDate } from "~/features/common/utils";
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
  SOURCE = "source",
  REQUEST_TYPE = "request_type",
  SUBJECT_IDENTITY = "subject_identity",
  TIME_RECEIVED = "created_at",
  CREATED_BY = "created_by",
  REVIEWER = "reviewer",
  ID = "id",
  LOCATION = "location",
  ACTIONS = "actions",
}

const columnHelper = createColumnHelper<PrivacyRequestEntity>();

export const getRequestTableColumns = () => [
  columnHelper.accessor((row) => row.status, {
    id: COLUMN_IDS.STATUS,
    cell: ({ getValue }) => <RequestStatusBadgeCell value={getValue()} />,
    header: (props) => <DefaultHeaderCell value="Status" {...props} />,
    size: 120,
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
    size: 80,
  }),
  columnHelper.accessor((row) => row.source, {
    id: COLUMN_IDS.SOURCE,
    cell: (props) =>
      props.getValue() ? (
        <BadgeCell value={props.getValue()!} />
      ) : (
        <DefaultCell value={undefined} />
      ),
    header: (props) => <DefaultHeaderCell value="Source" {...props} />,
    enableSorting: false,
  }),
  columnHelper.accessor((row) => row.policy.rules, {
    id: COLUMN_IDS.REQUEST_TYPE,
    cell: ({ getValue }) => <RequestActionTypeCell value={getValue()} />,
    header: (props) => <DefaultHeaderCell value="Request type" {...props} />,
    enableSorting: false,
    size: 100,
  }),
  columnHelper.accessor(
    (row) =>
      row.identity?.email?.value || row.identity?.phone_number?.value || "",
    {
      id: COLUMN_IDS.SUBJECT_IDENTITY,
      cell: ({ getValue }) => <DefaultCell value={getValue()} />,
      header: (props) => (
        <DefaultHeaderCell value="Subject identity" {...props} />
      ),
      enableSorting: false,
    },
  ),
  columnHelper.accessor((row) => row.created_at, {
    id: COLUMN_IDS.TIME_RECEIVED,
    cell: ({ getValue }) => <DefaultCell value={formatDate(getValue())} />,
    header: (props) => <DefaultHeaderCell value="Time received" {...props} />,
    size: 120,
  }),
  columnHelper.accessor((row) => row.reviewer?.username || "", {
    id: COLUMN_IDS.REVIEWER,
    cell: ({ getValue }) => (
      <DefaultCell value={getValue()} /> // NOTE: this field does not get set when reviewed as root user
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
  columnHelper.accessor((row) => row.location, {
    id: COLUMN_IDS.LOCATION,
    cell: ({ getValue }) => {
      const value = getValue();
      const isoEntry = value ? isoStringToEntry(value) : undefined;
      const formattedValue = isoEntry
        ? formatIsoLocation({ isoEntry, showFlag: true })
        : value;
      return <DefaultCell value={formattedValue} />;
    },
    header: (props) => <DefaultHeaderCell value="Location" {...props} />,
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
