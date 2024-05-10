import { Button, Heading, Stack, useDisclosure } from "@fidesui/react";
import React from "react";

import { ConfirmationModal } from "./ConfirmationModal";

export default {
  title: "Components/ConfirmationModal",
  component: ConfirmationModal,
};

export const ConfirmationModalStory = () => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  return (
    <Stack>
      <Heading size="md">Confirmation Modal</Heading>
      <Button colorScheme="primary" onClick={onOpen} width="fit-content">
        Open modal
      </Button>
      <ConfirmationModal
        isOpen={isOpen}
        onClose={onClose}
        title="My modal"
        message="Hey, welcome to my modal! Make yourself at home."
        onConfirm={onClose}
      />
    </Stack>
  );
};
