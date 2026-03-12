import { Button, DefaultOptionType, Flex, Modal, Typography } from "fidesui";
import { MouseEventHandler, useCallback, useState } from "react";

import { SystemSelect } from "~/features/common/dropdown/SystemSelect";
import { AddNewSystemModal } from "~/features/system/AddNewSystemModal";

const { Text } = Typography;

interface AssignSystemModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (selectedSystem?: DefaultOptionType) => void;
  isSaving?: boolean;
}

export const AssignSystemModal = ({
  isOpen,
  onSave,
  isSaving,
  onClose,
}: AssignSystemModalProps) => {
  const [selectedSystem, setSelectedSystem] = useState<DefaultOptionType>();
  const [isNewSystemModalOpen, setIsNewSystemModalOpen] = useState(false);

  const onAddSystem: MouseEventHandler<HTMLButtonElement> = useCallback((e) => {
    e.preventDefault();
    setIsNewSystemModalOpen(true);
  }, []);

  const handleCloseNewSystemModal = () => {
    setIsNewSystemModalOpen(false);
  };

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
      destroyOnClose
      footer={null}
      data-testid="add-modal-content"
    >
      <Flex vertical gap={20} className="pb-6 pt-4">
        <Text>
          Assign a system to the selected assets. If no system exists, select
          &apos;Add new system&apos; to create one.
        </Text>
        <SystemSelect
          placeholder="Search or select..."
          onSelect={(_, option) => {
            setSelectedSystem(option);
          }}
          onAddSystem={onAddSystem}
          value={selectedSystem}
        />
      </Flex>{" "}
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
      {isNewSystemModalOpen && (
        <AddNewSystemModal
          isOpen
          onClose={handleCloseNewSystemModal}
          onSuccessfulSubmit={(fidesKey, name) => {
            handleCloseNewSystemModal();
            setSelectedSystem({ label: name, value: fidesKey });
          }}
          toastOnSuccess
        />
      )}
    </Modal>
  );
};
