import {
  Modal,
  ModalBody,
  ModalContent,
  ModalHeader,
  ModalOverlay,
  Select,
  Text,
} from "fidesui";
import { useState } from "react";
import MessagingActionTypeLabelEnum from "~/features/messaging-templates/MessagingActionTypeLabelEnum";
import { MessagingActionType } from "~/types/api";

const AddMessagingTemplateModal = () => {
  const [selectedTemplate, setSelectedTemplate] = useState<string | undefined>(
    undefined
  );

  const messagingActionTypeIds = Object.keys(
    MessagingActionTypeLabelEnum
  ) as MessagingActionType[];

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="2xl" isCentered>
      <ModalOverlay />
      <ModalContent data-testid="add-messaging-template-modal">
        <ModalHeader>Select message template</ModalHeader>
        <ModalBody>
          <Text>
            Add a new email message by selecting a template below and clicking
            accept.
          </Text>
          <Text>Choose template:</Text>
          <Select
            placeholder="Select template"
            value={selectedTemplate}
            onChange={(e) => setSelectedTemplate(e.target.value)}
          >
            {messagingActionTypeIds.map((templateId) => (
              <option key={templateId} value={templateId}>
                {MessagingActionTypeLabelEnum[templateId]}
              </option>
            ))}
          </Select>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};
