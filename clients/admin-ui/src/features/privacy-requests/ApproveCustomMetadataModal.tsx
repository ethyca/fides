import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  Spacer,
  ModalCloseButton,
  ModalBody,
  Text,
  Button,
  ModalFooter,
  SimpleGrid,
  ListItem,
  UnorderedList,
  Tag,
  Flex,
} from "@fidesui/react";
import { snakeToSentenceCase } from "../common/utils";
import { PrivacyRequestEntity } from "./types";
import PII from "../common/PII";

interface Props {
  message: string;
  subjectRequest: PrivacyRequestEntity;
  isOpen: boolean;
  onClose: () => void;
}

const ApproveCustomMetadataModal = ({
  message,
  subjectRequest: { custom_metadata },
  isOpen,
  onClose,
}: Props) => (
  <Modal isOpen={isOpen} onClose={onClose} isCentered>
    <ModalOverlay />
    <ModalContent>
      <ModalHeader>
        <ModalCloseButton />
      </ModalHeader>
      <ModalBody paddingTop={0} paddingBottom={0}>
        <Text
          fontWeight="medium"
          fontSize="sm"
          textAlign="center"
          marginBottom={4}
        >
          {message}
        </Text>
        <UnorderedList>
          {custom_metadata &&
            Object.entries(custom_metadata).map(([key, value]) => (
              <ListItem key={key}>
                <Flex alignItems="flex-start" key={key}>
                  <Text mr={2} fontSize="sm" color="gray.900" fontWeight="500">
                    {snakeToSentenceCase(key)}:
                  </Text>
                  <Text color="gray.600" fontWeight="500" fontSize="sm" mr={2}>
                    {value} (Unverified)
                  </Text>
                </Flex>
              </ListItem>
            ))}
        </UnorderedList>
      </ModalBody>
      <ModalFooter>
        <SimpleGrid columns={2} width="100%">
          <Button variant="outline" size="sm" mr={3} data-testid="cancel-btn">
            Cancel
          </Button>
          <Button colorScheme="primary" size="sm" data-testid="continue-btn">
            Confirm
          </Button>
        </SimpleGrid>
      </ModalFooter>
    </ModalContent>
  </Modal>
);

export default ApproveCustomMetadataModal;
