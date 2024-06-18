import {
  Button,
  ButtonGroup,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Select,
  Text,
} from "fidesui";
import { useState } from "react";

import MessagingActionTypeLabelEnum from "~/features/messaging-templates/MessagingActionTypeLabelEnum";
import { MessagingActionType } from "~/types/api";

interface AddMessagingTemplateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAccept: (templateId: string) => void;
}

const AddMessagingTemplateModal: React.FC<AddMessagingTemplateModalProps> = ({
  isOpen,
  onClose,
  onAccept,
}) => {
  const [selectedTemplateId, setSelectedTemplateId] = useState<
    string | undefined
  >(undefined);

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
            value={selectedTemplateId}
            onChange={(e) => setSelectedTemplateId(e.target.value)}
          >
            {messagingActionTypeIds.map((templateId) => (
              <option key={templateId} value={templateId}>
                {MessagingActionTypeLabelEnum[templateId]}
              </option>
            ))}
          </Select>
        </ModalBody>
        <ModalFooter justifyContent="flex-start">
          <ButtonGroup size="sm">
            <Button
              variant="outline"
              mr={2}
              onClick={onClose}
              data-testid="cancel-btn"
            >
              Cancel
            </Button>
            <Button
              colorScheme="primary"
              onClick={() => onAccept(selectedTemplateId!)}
              data-testid="confirm-btn"
              disabled={!selectedTemplateId}
            >
              Confirm
            </Button>
          </ButtonGroup>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
export default AddMessagingTemplateModal;
