import { Button, Card, Flex, Tooltip, Typography, useModal } from "fidesui";

import { confirmDeletePolicy } from "~/features/policies/confirmDeletePolicy";
import { DEFAULT_POLICY_TOOLTIP } from "~/features/policies/constants";
import { PolicyResponse } from "~/types/api";

const { Title, Text } = Typography;

interface PolicyBoxProps {
  policy: PolicyResponse;
  isDefault?: boolean;
  onEdit?: () => void;
  onDelete?: () => void;
  isDeleting?: boolean;
}

export const PolicyBox = ({
  policy,
  isDefault = false,
  onEdit,
  onDelete,
  isDeleting = false,
}: PolicyBoxProps) => {
  const modal = useModal();

  return (
    <Card data-testid="policy-box">
      <Flex justify="space-between" align="flex-start">
        <Flex vertical gap="small">
          <Title level={5}>{policy.name}</Title>
          <Text type="secondary" code>
            {policy.key}
          </Text>
          {policy.execution_timeframe !== null && (
            <Text type="secondary">
              Execution timeframe: {policy.execution_timeframe} days
            </Text>
          )}
        </Flex>
        <Flex gap="small">
          {onEdit && (
            <Button onClick={onEdit} data-testid="edit-policy-btn">
              Edit
            </Button>
          )}
          {onDelete && (
            <Tooltip title={isDefault ? DEFAULT_POLICY_TOOLTIP : undefined}>
              <Button
                danger
                disabled={isDefault}
                onClick={() =>
                  confirmDeletePolicy(modal, policy.name, onDelete)
                }
                loading={isDeleting}
                data-testid="delete-policy-btn"
              >
                Delete
              </Button>
            </Tooltip>
          )}
        </Flex>
      </Flex>
    </Card>
  );
};
