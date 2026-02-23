import {
  Button,
  ChakraBox as Box,
  ChakraFlex as Flex,
  ChakraText as Text,
  Modal,
  Typography,
} from "fidesui";
import { useState } from "react";

import { PolicyResponse } from "~/types/api";

interface PolicyBoxProps {
  policy: PolicyResponse;
  onDelete?: () => void;
  isDeleting?: boolean;
}

const PolicyBox = ({
  policy,
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
      <Box
        borderWidth={1}
        borderColor="gray.200"
        borderRadius="lg"
        overflow="hidden"
        padding="16px"
        marginBottom="24px"
        data-testid={`policy-info-${policy.key}`}
      >
        <Flex justify="space-between" align="flex-start">
          <Flex direction="column" gap={2}>
            <Text fontSize="lg" fontWeight="semibold" color="gray.700">
              {policy.name}
            </Text>
            <Text fontSize="sm" color="gray.500" fontFamily="mono">
              {policy.key}
            </Text>
          </Flex>
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
      </Box>

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
        <Typography.Text type="secondary">
          Are you sure you want to delete the policy &ldquo;{policy.name}
          &rdquo;? This action cannot be undone and will also delete all
          associated rules.
        </Typography.Text>
      </Modal>
    </>
  );
};

export default PolicyBox;
