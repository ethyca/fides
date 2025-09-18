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

import { renderValue } from "../common/utils";
import { PrivacyRequestEntity } from "./types";

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
  const {
    identity,
    identity_verified_at: identityVerifiedAt,
    custom_privacy_request_fields: customPrivacyRequestFields,
  } = subjectRequest;
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
            {
              /*
               * Doing this despite what the api is saying
               * Casting to unknown to cover all bases until types are fixed
               */
              identity &&
                Object.entries(identity as Record<string, unknown>)
                  .filter(
                    ([, item]) =>
                      item &&
                      typeof item === "object" &&
                      "value" in item &&
                      !!item?.value,
                  )
                  .map(([key, item]) => {
                    const parsedValue =
                      item &&
                      typeof item === "object" &&
                      "value" in item &&
                      "label" in item &&
                      typeof item.label === "string"
                        ? item
                        : null;
                    const value = renderValue(parsedValue?.value);
                    const label =
                      typeof parsedValue?.label === "string" &&
                      parsedValue.label.toLocaleLowerCase();

                    return (
                      <ListItem key={key}>
                        <Flex key={key} alignItems="flex-start">
                          <Text
                            mr={2}
                            fontSize="sm"
                            color="gray.900"
                            fontWeight="500"
                          >
                            {label}:
                          </Text>
                          <Text
                            color="gray.600"
                            fontWeight="500"
                            fontSize="sm"
                            mr={2}
                          >
                            {value}
                          </Text>
                          ({identityVerifiedAt ? "Verified" : "Unverified"})
                        </Flex>
                      </ListItem>
                    );
                  })
            }
            {
              /*
               * Doing this despite what the api is saying
               * Casting to unknown to cover all bases until types are fixed
               */
              customPrivacyRequestFields &&
                Object.entries(
                  customPrivacyRequestFields as Record<string, unknown>,
                )
                  .filter(
                    ([, item]) =>
                      item &&
                      typeof item === "object" &&
                      "value" in item &&
                      !!item?.value,
                  )
                  .map(([key, item]) => {
                    const parsedValue =
                      item &&
                      typeof item === "object" &&
                      "value" in item &&
                      "label" in item &&
                      typeof item.label === "string"
                        ? item
                        : null;
                    const value = renderValue(parsedValue?.value);
                    const label =
                      typeof parsedValue?.label === "string" &&
                      parsedValue.label.toLocaleLowerCase();

                    return (
                      <ListItem key={key}>
                        <Flex alignItems="flex-start" key={key}>
                          <Text
                            mr={2}
                            fontSize="sm"
                            color="gray.900"
                            fontWeight="500"
                          >
                            {label}:
                          </Text>
                          <Text
                            color="gray.600"
                            fontWeight="500"
                            fontSize="sm"
                            mr={2}
                          >
                            {value}{" "}
                          </Text>
                          (Unverified)
                        </Flex>
                      </ListItem>
                    );
                  })
            }
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
