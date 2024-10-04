import { Select, SingleValue } from "chakra-react-select";
import {
  AntButton,
  Box,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Text,
} from "fidesui";
import { useState } from "react";

import { SELECT_STYLES } from "~/features/common/form/inputs";
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

          <Box data-testid="template-type-selector">
            <Select
              options={options}
              size="sm"
              chakraStyles={SELECT_STYLES}
              onChange={(option: SingleValue<any>) => {
                setSelectedTemplateType(option?.value);
              }}
              classNamePrefix="custom-select"
            />
          </Box>
        </ModalBody>
        <ModalFooter justifyContent="flex-start">
          <div className="flex w-full gap-4">
            <AntButton
              onClick={onClose}
              data-testid="cancel-btn"
              className="grow"
            >
              Cancel
            </AntButton>
            <AntButton
              onClick={() => onAccept(selectedTemplateId!)}
              type="primary"
              data-testid="confirm-btn"
              disabled={!selectedTemplateId}
              className="grow"
            >
              Next
            </AntButton>
          </div>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
export default AddMessagingTemplateModal;
