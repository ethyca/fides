import {
  AntButton as Button,
  AntDefaultOptionType as DefaultOptionType,
  AntFlex as Flex,
  AntTypography as Typography,
  ModalProps,
} from "fidesui";
import { MouseEventHandler, useCallback, useState } from "react";

import { SystemSelect } from "~/features/common/dropdown/SystemSelect";
import FormModal from "~/features/common/modals/FormModal";
import { AddNewSystemModal } from "~/features/system/AddNewSystemModal";

const { Text } = Typography;

interface AssignSystemModalProps extends Omit<ModalProps, "children"> {
  onSave: (selectedSystem?: DefaultOptionType) => void;
  isSaving?: boolean;
}

export const AssignSystemModal = ({
  onSave,
  isSaving,
  ...props
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
    props.onClose();
  };

  return (
    <FormModal title="Assign system" {...props} onClose={handleClose}>
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
    </FormModal>
  );
};
