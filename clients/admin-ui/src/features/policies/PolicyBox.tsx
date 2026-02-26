import { Button, Card, Flex, Typography, useModal } from "fidesui";

import { confirmDeletePolicy } from "~/features/policies/confirmDeletePolicy";
import { PolicyResponse } from "~/types/api";

const { Title, Text } = Typography;

interface PolicyBoxProps {
  policy: PolicyResponse;
  onEdit?: () => void;
  onDelete?: () => void;
  isDeleting?: boolean;
}

export const PolicyBox = ({
  policy,
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
            <Button
              danger
              onClick={() => confirmDeletePolicy(modal, policy.name, onDelete)}
              loading={isDeleting}
              data-testid="delete-policy-btn"
            >
              Delete
            </Button>
          )}
        </Flex>
      </Flex>
    </Card>
  );
};
