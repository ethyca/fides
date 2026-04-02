import {
  Button,
  Card,
  Divider,
  Dropdown,
  Flex,
  Icons,
  Paragraph,
  Switch,
  Tag,
  Text,
  Typography,
} from "fidesui";

import { DECISION_LABELS } from "./constants";
import { AccessPolicyListItem } from "./types";

const { Title } = Typography;

const formatRelativeTime = (isoDate?: string): string => {
  if (!isoDate) {
    return "—";
  }
  const diff = Date.now() - new Date(isoDate).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) {
    return "Just now";
  }
  if (minutes < 60) {
    return `${minutes}m ago`;
  }
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours}h ago`;
  }
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
};

interface PolicyCardProps {
  policy: AccessPolicyListItem;
  onToggle: (policy: AccessPolicyListItem) => void;
  onEdit: (policy: AccessPolicyListItem) => void;
  onDuplicate: (policy: AccessPolicyListItem) => void;
  onDelete: (policy: AccessPolicyListItem) => void;
}

const PolicyCard = ({
  policy,
  onToggle,
  onEdit,
  onDuplicate,
  onDelete,
}: PolicyCardProps) => {
  const menuItems = {
    items: [
      { key: "edit", label: "Edit", onClick: () => onEdit(policy) },
      {
        key: "duplicate",
        label: "Duplicate",
        onClick: () => onDuplicate(policy),
      },
      {
        key: "delete",
        label: "Delete",
        danger: true,
        onClick: () => onDelete(policy),
      },
    ],
  };

  return (
    <Card
      className="flex h-full flex-col"
      classNames={{ body: "flex flex-col flex-1" }}
    >
      <Flex vertical justify="space-between" className="flex-1">
        <Flex vertical gap="small">
          {/* Header */}
          <Flex justify="space-between" align="flex-start">
            <Flex gap="small" align="center" className="min-w-0">
              <Title level={5} className="!m-0 truncate">
                {policy.name}
              </Title>
            </Flex>
            <Flex align="center" gap="small" className="shrink-0">
              {policy.decision && (
                <Tag color={policy.decision === "ALLOW" ? "success" : "error"}>
                  {DECISION_LABELS[policy.decision] ?? policy.decision}
                </Tag>
              )}
              <Dropdown menu={menuItems} trigger={["click"]}>
                <Button
                  aria-label="Policy actions"
                  type="text"
                  size="small"
                  icon={<Icons.OverflowMenuVertical />}
                />
              </Dropdown>
            </Flex>
          </Flex>

          {/* Description */}
          <Paragraph type="secondary" className="!mb-0 line-clamp-3">
            {policy.description}
          </Paragraph>
        </Flex>

        <Flex vertical>
          <Divider className="!my-4" />

          {/* Footer */}
          <Flex justify="space-between" align="center">
            <Flex gap="small" align="center">
              <Switch
                aria-label="Policy enabled"
                checked={policy.enabled}
                onChange={() => onToggle(policy)}
                size="small"
              />
              <Text size="sm">Policy enabled</Text>
            </Flex>
            <Flex gap="small" align="center">
              <Icons.Time size={14} />
              <Text type="secondary" size="sm">
                {formatRelativeTime(policy.updated_at)}
              </Text>
            </Flex>
          </Flex>
        </Flex>
      </Flex>
    </Card>
  );
};

export default PolicyCard;
