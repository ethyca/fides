import {
  Card,
  Divider,
  Flex,
  Icons,
  Paragraph,
  Switch,
  Tag,
  Text,
  Tooltip,
  Typography,
} from "fidesui";
import NextLink from "next/link";

import { DECISION_LABELS } from "./constants";
import styles from "./PolicyCard.module.scss";
import { AccessPolicyListItem, ActionType } from "./types";
import { formatRelativeTime } from "./utils";

const { Link: LinkText } = Typography;

interface PolicyCardProps {
  policy: AccessPolicyListItem;
  onToggle: (policy: AccessPolicyListItem) => void;
}

const PolicyCard = ({ policy, onToggle }: PolicyCardProps) => {
  return (
    <Card className={`flex h-full flex-col ${styles.card}`}>
      <Flex vertical justify="space-between" className="flex-1">
        <Flex vertical gap="small">
          {/* Header */}
          <Flex justify="space-between" align="flex-start">
            <Flex gap="small" align="center" className="min-w-0">
              {/* legacyBehavior is required: Typography.Link renders <a>, and
                  Next.js 13 Link also renders <a> — without it we'd get nested anchors */}
              <NextLink
                href={`/access-policies/edit/${policy.id}`}
                passHref
                legacyBehavior
              >
                <LinkText
                  strong
                  ellipsis
                  variant="primary"
                  className={styles.policyName}
                >
                  {policy.name}
                </LinkText>
              </NextLink>
            </Flex>
            <Flex gap="small" align="center" className="shrink-0">
              {policy.is_recommendation && (
                <Tooltip title="Recommended by Fides based on your configuration">
                  <Tag color="sandstone" hasSparkle />
                </Tooltip>
              )}
              {policy.decision && (
                <Tag
                  color={
                    policy.decision === ActionType.ALLOW ? "success" : "error"
                  }
                >
                  {DECISION_LABELS[policy.decision] ?? policy.decision}
                </Tag>
              )}
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
              <Text size="sm">Enabled</Text>
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
