import { Button, Icons, List, Space, Typography, useModal } from "fidesui";
import Link from "next/link";
import { useMemo } from "react";

import { useGetPoliciesQuery } from "~/features/policies/policy.slice";

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
  onDeleteAction: (policyKey: string) => void;
}

const fieldCountLabel = (count: number) =>
  count === 1 ? "1 field" : `${count} fields`;

export const ActionsTable = ({
  propertyId,
  actions,
  onEditAction,
  onAddAction,
  onDeleteAction,
}: ActionsTableProps) => {
  const modal = useModal();
  const { data: policiesPage } = useGetPoliciesQuery();
  const policyNameByKey = useMemo(() => {
    const map: Record<string, string> = {};
    policiesPage?.items?.forEach((p) => {
      if (p.key) {
        map[p.key] = p.name ?? p.key;
      }
    });
    return map;
  }, [policiesPage]);

  const handleDeleteClick = (action: ActionFormValues) => {
    modal.confirm({
      title: "Delete action?",
      content: (
        <span>
          This will remove{" "}
          <Typography.Text code>
            {action.title || action.policy_key}
          </Typography.Text>{" "}
          and its associated form fields from this property. This change is
          saved immediately and cannot be undone.
        </span>
      ),
      okText: "Delete",
      okButtonProps: { danger: true },
      centered: true,
      onOk: () => onDeleteAction(action.policy_key),
    });
  };

  return (
    <Space orientation="vertical" style={{ width: "100%" }}>
      <Button onClick={onAddAction}>Add action</Button>
      <List
        bordered
        dataSource={actions}
        rowKey="policy_key"
        renderItem={(row) => {
          const fieldCount = Object.keys(
            row.custom_privacy_request_fields ?? {},
          ).length;
          return (
            <List.Item
              key={row.policy_key}
              actions={[
                ...(propertyId
                  ? [
                      <Link
                        key="edit-form"
                        href={`/properties/${propertyId}/forms/${encodeURIComponent(
                          row.policy_key,
                        )}`}
                      >
                        <Button>Edit form</Button>
                      </Link>,
                    ]
                  : []),
                <Button
                  key="edit-action"
                  icon={<Icons.Edit />}
                  onClick={() => onEditAction(row)}
                  aria-label={`Edit action ${row.title || row.policy_key}`}
                  data-testid={`edit-action-${row.policy_key}`}
                />,
                <Button
                  key="delete-action"
                  icon={<Icons.TrashCan />}
                  onClick={() => handleDeleteClick(row)}
                  aria-label={`Delete action ${row.title || row.policy_key}`}
                  data-testid={`delete-action-${row.policy_key}`}
                />,
              ]}
            >
              <List.Item.Meta
                title={row.title || row.policy_key}
                description={
                  <Space size="small">
                    <Typography.Text type="secondary">
                      {policyNameByKey[row.policy_key] ?? row.policy_key}
                    </Typography.Text>
                    <Typography.Text type="secondary">·</Typography.Text>
                    <Typography.Text type="secondary">
                      {fieldCountLabel(fieldCount)}
                    </Typography.Text>
                  </Space>
                }
              />
            </List.Item>
          );
        }}
      />
    </Space>
  );
};
