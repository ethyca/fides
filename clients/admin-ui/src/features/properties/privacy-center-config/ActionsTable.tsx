import { Button, Space, Table } from "fidesui";
import Link from "next/link";

import type { ActionFormValues } from "./ActionEditModal";

interface ActionsTableProps {
  propertyId: string;
  actions: Array<
    ActionFormValues & {
      custom_privacy_request_fields?: Record<string, unknown>;
    }
  >;
  onEditAction: (action: ActionFormValues) => void;
  onAddAction: () => void;
}

export const ActionsTable: React.FC<ActionsTableProps> = ({
  propertyId,
  actions,
  onEditAction,
  onAddAction,
}) => {
  const columns = [
    { title: "Action", dataIndex: "title", key: "title" },
    { title: "Policy key", dataIndex: "policy_key", key: "policy_key" },
    {
      title: "Fields",
      key: "fields",
      render: (_: unknown, row: (typeof actions)[number]) => {
        const count = Object.keys(row.custom_privacy_request_fields ?? {}).length;
        return count === 1 ? "1 field" : `${count} fields`;
      },
    },
    {
      title: "",
      key: "actions",
      render: (_: unknown, row: (typeof actions)[number]) => (
        <Space>
          <Link
            href={`/properties/${propertyId}/forms/${encodeURIComponent(
              row.policy_key,
            )}`}
          >
            <Button>Edit form</Button>
          </Link>
          <Button onClick={() => onEditAction(row)}>Edit action</Button>
        </Space>
      ),
    },
  ];

  return (
    <Space direction="vertical" style={{ width: "100%" }}>
      <Button onClick={onAddAction}>Add action</Button>
      <Table
        rowKey="policy_key"
        dataSource={actions}
        columns={columns}
        pagination={false}
      />
    </Space>
  );
};
