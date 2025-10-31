import {
  AntButton as Button,
  Flex,
  ListItem,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  SimpleGrid,
  Text,
  UnorderedList,
} from "fidesui";
import React, { useCallback } from "react";

import { PrivacyRequestResponse } from "~/types/api";

import {
  getCustomFields,
  getOtherIdentities,
  getPrimaryIdentity,
} from "./utils";

type ApproveModalProps = {
  isOpen: boolean;
  onClose: () => void;
  onApproveRequest: () => Promise<any>;
  isLoading: boolean;
  subjectRequest: PrivacyRequestResponse;
};

const ApprovePrivacyRequestModal = ({
  isOpen,
  onClose,
  onApproveRequest,
  isLoading,
  subjectRequest,
}: ApproveModalProps) => {
  const {
    identity,
    identity_verified_at: identityVerifiedAt,
    custom_privacy_request_fields: customPrivacyRequestFields,
  } = subjectRequest;

  const primaryIdentity = getPrimaryIdentity(identity);
  const otherIdentities = getOtherIdentities(identity, primaryIdentity);
  const allIdentities = [
    ...(primaryIdentity ? [primaryIdentity] : []),
    ...otherIdentities,
  ];
  const customFields = getCustomFields(customPrivacyRequestFields);

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
            {allIdentities.map((identityItem) => (
              <ListItem key={identityItem.key}>
                <Flex alignItems="flex-start">
                  <Text mr={2} fontSize="sm" color="gray.900" fontWeight="500">
                    {identityItem.label}:
                  </Text>
                  <Text color="gray.600" fontWeight="500" fontSize="sm" mr={2}>
                    {identityItem.value}
                  </Text>
                  ({identityVerifiedAt ? "Verified" : "Unverified"})
                </Flex>
              </ListItem>
            ))}
            {customFields.map((field) => (
              <ListItem key={field.key}>
                <Flex alignItems="flex-start">
                  <Text mr={2} fontSize="sm" color="gray.900" fontWeight="500">
                    {field.label}:
                  </Text>
                  <Text color="gray.600" fontWeight="500" fontSize="sm" mr={2}>
                    {Array.isArray(field.value)
                      ? field.value.join(", ")
                      : String(field.value)}
                  </Text>
                  (Unverified)
                </Flex>
              </ListItem>
            ))}
          </UnorderedList>
        </ModalBody>
        <ModalFooter>
          <SimpleGrid columns={2} width="100%">
            <Button onClick={onClose} className="mr-3" data-testid="cancel-btn">
              Cancel
            </Button>
            <Button
              type="primary"
              data-testid="continue-btn"
              onClick={handleSubmit}
              loading={isLoading}
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
