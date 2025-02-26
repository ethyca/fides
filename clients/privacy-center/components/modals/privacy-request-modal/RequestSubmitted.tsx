import {
  Button,
  HStack,
  Image,
  ModalBody,
  ModalFooter,
  ModalHeader,
  Text,
} from "fidesui";
import React from "react";

type RequestSubmittedProps = {
  onClose: () => void;
};

const RequestSubmitted = ({ onClose }: RequestSubmittedProps) => (
  <>
    <HStack justifyContent="center" data-testid="request-submitted">
      <Image
        mt="24px"
        src="/green-check.svg"
        alt="green-checkmark"
        width="48px"
        height="48px"
      />
    </HStack>
    <ModalHeader
      pt={6}
      pb={0}
      textAlign="center"
      data-testid="request-submitted"
    >
      Request submitted
    </ModalHeader>

    <ModalBody>
      <Text fontSize="sm" color="gray.500" mb={4}>
        Thanks for your request. A member of our team will review and be in
        contact with you shortly.
      </Text>
    </ModalBody>

    <ModalFooter pb={6}>
      <Button
        flex="1"
        bg="primary.800"
        _hover={{ bg: "primary.400" }}
        _active={{ bg: "primary.500" }}
        colorScheme="primary"
        size="sm"
        onClick={onClose}
      >
        Continue
      </Button>
    </ModalFooter>
  </>
);

export default RequestSubmitted;
