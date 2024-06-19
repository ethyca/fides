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

import { CustomizableMessagingTemplatesEnum } from "~/features/messaging-templates/CustomizableMessagingTemplatesEnum";
import CustomizableMessagingTemplatesLabelEnum from "~/features/messaging-templates/CustomizableMessagingTemplatesLabelEnum";

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
    CustomizableMessagingTemplatesLabelEnum
  ) as CustomizableMessagingTemplatesEnum[];

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="2xl" isCentered>
      <ModalOverlay />
      <ModalContent data-testid="add-messaging-template-modal">
        <ModalHeader borderBottomWidth={1} fontWeight="bold">
          Select message template
        </ModalHeader>
        <ModalBody>
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
          <Text
            color="gray.700"
            fontSize="sm"
            fontWeight="medium"
            marginBottom={2}
          >
            Choose template:
          </Text>
          <Select
            placeholder="Select a template"
            value={selectedTemplateId}
            onChange={(e) => setSelectedTemplateId(e.target.value)}
            color="gray.500"
          >
            {messagingActionTypeIds.map((templateId) => (
              <option key={templateId} value={templateId}>
                {CustomizableMessagingTemplatesLabelEnum[templateId]}
              </option>
            ))}
          </Select>
        </ModalBody>
        <ModalFooter justifyContent="flex-start">
          <ButtonGroup size="sm" display="flex" justifyItems="stretch" w="full">
            <Button
              variant="outline"
              mr={2}
              onClick={onClose}
              data-testid="cancel-btn"
              size="md"
              flex={1}
            >
              Cancel
            </Button>
            <Button
              size="md"
              colorScheme="primary"
              bgColor="primary.800"
              onClick={() => onAccept(selectedTemplateId!)}
              data-testid="confirm-btn"
              disabled={!selectedTemplateId}
              flex={1}
            >
              Next
            </Button>
          </ButtonGroup>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
export default AddMessagingTemplateModal;
