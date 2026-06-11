import { Button, DefaultOptionType, Flex, Modal, Typography } from "fidesui";
import { useState } from "react";

import { MockSystemSelect } from "./MockSystemSelect";

const { Text } = Typography;

interface MockAssignSystemModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (selectedSystem?: DefaultOptionType) => void;
  isSaving?: boolean;
}

/**
 * Bulk-assign modal for the AWS cloud-infra prototype. Mirrors AssignSystemModal
 * but sources its options from the mock AWS / business-application catalog
 * (with logos) instead of the live systems API.
 */
export const MockAssignSystemModal = ({
  isOpen,
  onSave,
  isSaving,
  onClose,
}: MockAssignSystemModalProps) => {
  const [selectedSystem, setSelectedSystem] = useState<DefaultOptionType>();

  const handleClose = () => {
    setSelectedSystem(undefined);
    onClose();
  };

  return (
    <Modal
      title="Assign system"
      open={isOpen}
      onCancel={handleClose}
      centered
      destroyOnHidden
      footer={null}
      data-testid="add-modal-content"
    >
      <Flex vertical gap={20} className="pb-6 pt-4">
        <Text>Assign a system to the selected resources.</Text>
        <MockSystemSelect
          placeholder="Search or select..."
          labelInValue
          onSelect={(_, option) => setSelectedSystem(option)}
          value={selectedSystem}
        />
      </Flex>
      <Flex justify="space-between">
        <Button htmlType="reset" onClick={handleClose} data-testid="cancel-btn">
          Cancel
        </Button>
        <Button
          htmlType="submit"
          type="primary"
          disabled={!selectedSystem}
          loading={isSaving}
          onClick={() => {
            onSave(selectedSystem);
            handleClose();
          }}
          data-testid="save-btn"
        >
          Save
        </Button>
      </Flex>
    </Modal>
  );
};
