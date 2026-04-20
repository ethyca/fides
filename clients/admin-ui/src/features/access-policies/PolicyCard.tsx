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
} from "fidesui";

import { RouterLink } from "~/features/common/nav/RouterLink";
import { ACCESS_POLICY_EDIT_ROUTE } from "~/features/common/nav/routes";

import DecisionTag from "./DecisionTag";
import styles from "./PolicyCard.module.scss";
import { AccessPolicyListItem } from "./types";
import { formatRelativeTime } from "./utils";

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
              <RouterLink
                href={{
                  pathname: ACCESS_POLICY_EDIT_ROUTE,
                  query: { id: policy.id },
                }}
                strong
                ellipsis
                variant="primary"
                className={styles.policyName}
              >
                {policy.name}
              </RouterLink>
            </Flex>
            <Flex gap="small" align="center" className="shrink-0">
              {policy.is_recommendation && (
                <Tooltip title="Recommended by Fides based on your configuration">
                  <Tag color="sandstone" hasSparkle />
                </Tooltip>
              )}
              {policy.decision && <DecisionTag decision={policy.decision} />}
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
