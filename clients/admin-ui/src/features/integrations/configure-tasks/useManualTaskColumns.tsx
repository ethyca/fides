import {
  AntButton as Button,
  AntFlex as Flex,
  AntTypography as Typography,
  Icons,
} from "fidesui";
import { useMemo } from "react";

import { FIELD_TYPE_LABELS, REQUEST_TYPE_LABELS } from "./constants";
import { Task } from "./types";

interface UseManualTaskColumnsProps {
  onEdit: (task: Task) => void;
  onDelete: (task: Task) => void;
}

export const useManualTaskColumns = ({
  onEdit,
  onDelete,
}: UseManualTaskColumnsProps) => {
  const columns = useMemo(
    () => [
      {
        title: "Task Name",
        dataIndex: "name",
        key: "name",
        ellipsis: {
          showTitle: false,
        },
        render: (text: string) => (
          <Typography.Text
            ellipsis={{ tooltip: text }}
            style={{ maxWidth: 200 }}
          >
            {text}
          </Typography.Text>
        ),
      },
      {
        title: "Description",
        dataIndex: "description",
        key: "description",
        ellipsis: {
          showTitle: false,
        },
        render: (text: string) => (
          <Typography.Text
            ellipsis={{ tooltip: text }}
            style={{ maxWidth: 300 }}
          >
            {text}
          </Typography.Text>
        ),
      },
      {
        title: "Field Type",
        dataIndex: "fieldType",
        key: "fieldType",
        render: (fieldType: string) => {
          return (
            FIELD_TYPE_LABELS[fieldType as keyof typeof FIELD_TYPE_LABELS] ||
            fieldType
          );
        },
      },
      {
        title: "Request Type",
        dataIndex: "requestType",
        key: "requestType",
        render: (requestType: string) => {
          return (
            REQUEST_TYPE_LABELS[
              requestType as keyof typeof REQUEST_TYPE_LABELS
            ] || requestType
          );
        },
      },
      {
        title: "Actions",
        key: "actions",
        render: (_: unknown, record: Task) => (
          <Flex gap={8}>
            <Button
              size="small"
              icon={<Icons.Edit />}
              onClick={() => onEdit(record)}
              data-testid="edit-btn"
            />
            <Button
              size="small"
              danger
              icon={<Icons.TrashCan />}
              onClick={() => onDelete(record)}
              data-testid="delete-btn"
            />
          </Flex>
        ),
      },
    ],
    [onEdit, onDelete],
  );

  return { columns };
};
