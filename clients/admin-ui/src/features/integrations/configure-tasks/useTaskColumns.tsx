import { ColumnDef, createColumnHelper } from "@tanstack/react-table";
import {
  AntButton as Button,
  AntTypography as Typography,
  Flex,
  Icons,
} from "fidesui";
import { useMemo } from "react";

import { DefaultCell, DefaultHeaderCell } from "~/features/common/table/v2";
import { ManualFieldRequestType, ManualTaskFieldType } from "~/types/api";

// Label mappings for field types and request types
const FIELD_TYPE_LABELS: Record<ManualTaskFieldType, string> = {
  [ManualTaskFieldType.TEXT]: "Text",
  [ManualTaskFieldType.CHECKBOX]: "Checkbox",
  [ManualTaskFieldType.ATTACHMENT]: "Attachment",
};

const REQUEST_TYPE_LABELS: Record<ManualFieldRequestType, string> = {
  [ManualFieldRequestType.ACCESS]: "Access",
  [ManualFieldRequestType.ERASURE]: "Erasure",
};

interface Task {
  id: string;
  name: string;
  description: string;
  fieldType: string;
  requestType: string;
  originalField: any;
}

const columnHelper = createColumnHelper<Task>();

// Table cell renderers
const renderTaskNameCell = (props: any) => (
  <div style={{ maxWidth: "200px" }}>
    <Typography.Text ellipsis={{ tooltip: props.getValue() }}>
      {props.getValue()}
    </Typography.Text>
  </div>
);

const renderDescriptionCell = (props: any) => (
  <div style={{ maxWidth: "300px" }}>
    <Typography.Text ellipsis={{ tooltip: props.getValue() }}>
      {props.getValue()}
    </Typography.Text>
  </div>
);

const renderFieldTypeCell = (props: any) => {
  const fieldType = props.getValue() as ManualTaskFieldType;
  const label = FIELD_TYPE_LABELS[fieldType] || fieldType;
  return <DefaultCell value={label} />;
};

const renderRequestTypeCell = (props: any) => {
  const requestType = props.getValue() as ManualFieldRequestType;
  const label = REQUEST_TYPE_LABELS[requestType] || requestType;
  return <DefaultCell value={label} />;
};

const renderActionsCell = (
  handleEdit: (task: Task) => void,
  handleDelete: (task: Task) => void,
) => {
  return function ActionsCell({ row }: any) {
    const task = row.original;
    return (
      <Flex gap={2}>
        <Button
          size="small"
          icon={<Icons.Edit />}
          onClick={() => handleEdit(task)}
        />
        <Button
          size="small"
          danger
          icon={<Icons.TrashCan />}
          onClick={() => handleDelete(task)}
        />
      </Flex>
    );
  };
};

// Header renderers
const renderTaskNameHeader = (props: any) => (
  <DefaultHeaderCell value="Task Name" {...props} />
);
const renderDescriptionHeader = (props: any) => (
  <DefaultHeaderCell value="Description" {...props} />
);
const renderFieldTypeHeader = (props: any) => (
  <DefaultHeaderCell value="Field Type" {...props} />
);
const renderRequestTypeHeader = (props: any) => (
  <DefaultHeaderCell value="Request Type" {...props} />
);
const renderActionsHeader = (props: any) => (
  <DefaultHeaderCell value="Actions" {...props} />
);

interface UseTaskColumnsProps {
  onEdit: (task: Task) => void;
  onDelete: (task: Task) => void;
}

export const useTaskColumns = ({ onEdit, onDelete }: UseTaskColumnsProps) => {
  const columns: ColumnDef<Task, any>[] = useMemo(
    () => [
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: renderTaskNameCell,
        header: renderTaskNameHeader,
      }),
      columnHelper.accessor((row) => row.description, {
        id: "description",
        cell: renderDescriptionCell,
        header: renderDescriptionHeader,
      }),
      columnHelper.accessor((row) => row.fieldType, {
        id: "fieldType",
        cell: renderFieldTypeCell,
        header: renderFieldTypeHeader,
      }),
      columnHelper.accessor((row) => row.requestType, {
        id: "requestType",
        cell: renderRequestTypeCell,
        header: renderRequestTypeHeader,
      }),
      columnHelper.display({
        id: "actions",
        cell: renderActionsCell(onEdit, onDelete),
        header: renderActionsHeader,
        meta: { disableRowClick: true },
      }),
    ],
    [onEdit, onDelete],
  );

  return { columns };
};

export type { Task };
