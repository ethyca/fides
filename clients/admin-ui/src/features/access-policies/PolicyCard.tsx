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

import { ControlGroup } from "./access-policies.slice";
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
  controlGroups: ControlGroup[];
  onToggle: (policy: AccessPolicyListItem) => void;
  onEdit: (policy: AccessPolicyListItem) => void;
  onDuplicate: (policy: AccessPolicyListItem) => void;
  onDelete: (policy: AccessPolicyListItem) => void;
}

const PolicyCard = ({
  policy,
  controlGroups,
  onToggle,
  onEdit,
  onDuplicate,
  onDelete,
}: PolicyCardProps) => {
  const controlGroupMap = new Map(
    controlGroups.map((cg) => [cg.key, cg.label]),
  );

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
    <Card className="flex h-full flex-col">
      <Flex vertical gap="small" className="flex-1">
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
                {policy.decision}
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

        {/* Controls tags */}
        {policy.controls && policy.controls.length > 0 && (
          <Flex wrap gap={4}>
            {policy.controls.map((key) => (
              <Tag key={key}>{controlGroupMap.get(key) ?? key}</Tag>
            ))}
          </Flex>
        )}

        {/* Spacer to push footer to bottom */}
        <div className="mt-auto" />

        <Divider className="!my-3" />

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
    </Card>
  );
};

export default PolicyCard;
