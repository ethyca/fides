import { Button, Card, Flex, Modal, Typography } from "fidesui";
import { useState } from "react";

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
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);

  const handleConfirmDelete = () => {
    onDelete?.();
    setIsDeleteModalOpen(false);
  };

  return (
    <>
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
                onClick={() => setIsDeleteModalOpen(true)}
                loading={isDeleting}
                data-testid="delete-policy-btn"
              >
                Delete
              </Button>
            )}
          </Flex>
        </Flex>
      </Card>

      <Modal
        title="Delete policy"
        open={isDeleteModalOpen}
        onCancel={() => setIsDeleteModalOpen(false)}
        onOk={handleConfirmDelete}
        okText="Delete"
        okButtonProps={{ danger: true }}
        cancelText="Cancel"
        centered
      >
        <Text type="secondary">
          Are you sure you want to delete the policy &ldquo;{policy.name}
          &rdquo;? This action cannot be undone and will also delete all
          associated rules.
        </Text>
      </Modal>
    </>
  );
};
