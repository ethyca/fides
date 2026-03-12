import {
  Badge,
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

import { PolicyItem } from "./types";

const { Title } = Typography;

interface PolicyCardProps {
  policy: PolicyItem;
  onToggle: (id: string) => void;
}

const PolicyCard = ({ policy, onToggle }: PolicyCardProps) => {
  const menuItems = {
    items: [
      { key: "edit", label: "Edit" },
      { key: "duplicate", label: "Duplicate" },
      { key: "delete", label: "Delete", danger: true },
    ],
  };

  return (
    <Card className="flex h-full flex-col">
      <Flex vertical gap="small" className="flex-1">
        {/* Header */}
        <Flex justify="space-between" align="flex-start">
          <Flex gap="small" align="center" className="min-w-0">
            <Title level={5} className="!m-0 truncate">
              {policy.title}
            </Title>
            {policy.isRecommendation && (
              <Tag color="sandstone" hasSparkle className="shrink-0" />
            )}
          </Flex>
          <Flex align="center" gap="small" className="shrink-0">
            {policy.isNew && (
              <Flex align="center" gap={4}>
                <Badge color="var(--fidesui-success)" />
                <Text size="sm" type="success">
                  New
                </Text>
              </Flex>
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

        {/* Stats — pushed to bottom */}
        <Flex align="center" gap="small" className="mt-auto">
          <Text size="sm">
            <Text strong size="sm">
              Violations:
            </Text>{" "}
            <Text
              size="sm"
              type={policy.violationCount > 0 ? undefined : "secondary"}
            >
              {policy.violationCount}
            </Text>
          </Text>
          {policy.violationCount > 0 && (
            <Button type="link" className="!p-0 !text-xs" size="small">
              View details
            </Button>
          )}
        </Flex>

        <Divider className="!my-3" />

        {/* Footer */}
        <Flex justify="space-between" align="center">
          <Flex gap="small" align="center">
            <Switch
              aria-label="Policy enabled"
              checked={policy.isEnabled}
              onChange={() => onToggle(policy.id)}
              size="small"
            />
            <Text size="sm">Policy enabled</Text>
          </Flex>
          <Flex gap="small" align="center">
            <Icons.Time size={14} />
            <Text type="secondary" size="sm">
              {policy.lastUpdated}
            </Text>
          </Flex>
        </Flex>
      </Flex>
    </Card>
  );
};

export default PolicyCard;
