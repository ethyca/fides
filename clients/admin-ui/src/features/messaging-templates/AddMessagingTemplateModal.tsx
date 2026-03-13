import {
  Button,
  ChakraBox as Box,
  ChakraText as Text,
  Modal,
  Select,
} from "fidesui";
import { useState } from "react";

import { MODAL_SIZE } from "~/features/common/modals/modal-sizes";
import { CustomizableMessagingTemplatesEnum } from "~/features/messaging-templates/CustomizableMessagingTemplatesEnum";
import CustomizableMessagingTemplatesLabelEnum from "~/features/messaging-templates/CustomizableMessagingTemplatesLabelEnum";

interface AddMessagingTemplateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAccept: (templateId: string) => void;
}

const AddMessagingTemplateModal = ({
  isOpen,
  onClose,
  onAccept,
}: AddMessagingTemplateModalProps) => {
  const [selectedTemplateId, setSelectedTemplateType] = useState<
    string | undefined
  >(undefined);

  const messagingActionTypeIds = Object.keys(
    CustomizableMessagingTemplatesLabelEnum,
  ) as CustomizableMessagingTemplatesEnum[];

  const options = messagingActionTypeIds.map((templateTypeId) => ({
    value: templateTypeId,
    label: CustomizableMessagingTemplatesLabelEnum[templateTypeId],
  }));

  return (
    <Modal
      open={isOpen}
      onCancel={onClose}
      centered
      destroyOnClose
      width={MODAL_SIZE.md}
      data-testid="add-messaging-template-modal"
      title="Select message template"
      footer={
        <div className="flex w-full gap-4">
          <Button onClick={onClose} data-testid="cancel-btn" className="grow">
            Cancel
          </Button>
          <Button
            onClick={() => onAccept(selectedTemplateId!)}
            type="primary"
            data-testid="confirm-btn"
            disabled={!selectedTemplateId}
            className="grow"
          >
            Next
          </Button>
        </div>
      }
    >
      <Text
        color="gray.700"
        fontWeight="medium"
        fontSize="sm"
        marginBottom={3}
        marginTop={1}
      >
        Add a new email message by selecting a template below and clicking
        accept.
      </Text>
      <Text color="gray.700" fontSize="sm" fontWeight="medium" marginBottom={2}>
        Choose template:
      </Text>

      <Box data-testid="template-type-selector">
        <Select<string>
          options={options}
          onChange={(value) => {
            setSelectedTemplateType(value);
          }}
          className="w-full"
          aria-label="Select a template"
        />
      </Box>
    </Modal>
  );
};
export default AddMessagingTemplateModal;
