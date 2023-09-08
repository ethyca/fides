import React, { useCallback } from "react";
import { PrivacyRequestEntity } from "./types";
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  UnorderedList,
  ListItem,
  Flex,
  ModalFooter,
  SimpleGrid,
  Button,
  Text,
} from "@fidesui/react";

type ApproveModalProps = {
  isOpen: boolean;
  onClose: () => void;
  onApproveRequest: () => Promise<any>;
  isLoading: boolean;
  subjectRequest: PrivacyRequestEntity;
};

const ApprovePrivacyRequestModal = ({
  isOpen,
  onClose,
  onApproveRequest,
  isLoading,
  subjectRequest,
}: ApproveModalProps) => {
  const { identity, identity_verified_at, custom_privacy_request_fields } =
    subjectRequest;
  const handleSubmit = useCallback(() => {
    onApproveRequest().then(() => {
      onClose();
    });
  }, [onApproveRequest, onClose]);

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg" isCentered>
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>Privacy request approval</ModalHeader>
        <ModalBody paddingTop={0} paddingBottom={0}>
          <Text color="gray.500" fontSize="14px" marginBottom={4}>
            Are you sure you want to approve this privacy request?
          </Text>
          <UnorderedList>
            {identity.email && identity_verified_at && (
              <ListItem>
                <Flex alignItems="flex-start">
                  <Text mr={2} fontSize="sm" color="gray.900" fontWeight="500">
                    Email:
                  </Text>
                  <Text color="gray.600" fontWeight="500" fontSize="sm" mr={2}>
                    {identity.email} (Verified)
                  </Text>
                </Flex>
              </ListItem>
            )}
            {identity.phone_number && identity_verified_at && (
              <ListItem>
                <Flex alignItems="flex-start">
                  <Text mr={2} fontSize="sm" color="gray.900" fontWeight="500">
                    Phone Number:
                  </Text>
                  <Text color="gray.600" fontWeight="500" fontSize="sm" mr={2}>
                    {identity.phone_number} (Verified)
                  </Text>
                </Flex>
              </ListItem>
            )}
            {custom_privacy_request_fields &&
              Object.entries(custom_privacy_request_fields)
                .filter(([key, item]) => item["value"])
                .map(([key, item]) => (
                  <ListItem key={key}>
                    <Flex alignItems="flex-start" key={key}>
                      <Text
                        mr={2}
                        fontSize="sm"
                        color="gray.900"
                        fontWeight="500"
                      >
                        {item["label"]}:
                      </Text>
                      <Text
                        color="gray.600"
                        fontWeight="500"
                        fontSize="sm"
                        mr={2}
                      >
                        {item["value"]} (Unverified)
                      </Text>
                    </Flex>
                  </ListItem>
                ))}
          </UnorderedList>
        </ModalBody>
        <ModalFooter>
          <SimpleGrid columns={2} width="100%">
            <Button
              variant="outline"
              size="sm"
              mr={3}
              data-testid="cancel-btn"
              onClick={onClose}
            >
              Cancel
            </Button>
            <Button
              colorScheme="primary"
              variant="solid"
              size="sm"
              data-testid="continue-btn"
              onClick={handleSubmit}
              isLoading={isLoading}
            >
              Confirm
            </Button>
          </SimpleGrid>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default ApprovePrivacyRequestModal;
