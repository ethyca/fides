import { Button, Flex, Modal, Select, Typography } from "fidesui";
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
      destroyOnHidden
      width={MODAL_SIZE.md}
      data-testid="add-messaging-template-modal"
      title="Select message template"
      footer={null}
    >
      <Typography.Paragraph>
        Add a new email message by selecting a template below and clicking
        accept.
      </Typography.Paragraph>
      <Select<string>
        data-testid="template-type-selector"
        options={options}
        onChange={(value) => {
          setSelectedTemplateType(value);
        }}
        className="w-full"
        placeholder="Choose template"
        aria-label="Select a template"
      />
      <Flex justify="flex-end" className="mt-4" gap="small">
        <Button onClick={onClose} data-testid="cancel-btn">
          Cancel
        </Button>
        <Button
          onClick={() => onAccept(selectedTemplateId!)}
          type="primary"
          data-testid="confirm-btn"
          disabled={!selectedTemplateId}
        >
          Next
        </Button>
      </Flex>
    </Modal>
  );
};
export default AddMessagingTemplateModal;
