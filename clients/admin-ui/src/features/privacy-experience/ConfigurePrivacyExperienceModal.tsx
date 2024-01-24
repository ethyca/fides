import {
  ArrowBackIcon,
  ArrowForwardIcon,
  Box,
  Button,
  Flex,
  Modal,
  ModalCloseButton,
  ModalContent,
  Text,
  VStack,
} from "@fidesui/react";
import { useState } from "react";

type ModalState = "none" | "configure" | "style";

const ConfigurePrivacyExperienceModal = ({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) => {
  const [modalState, setModalState] = useState<ModalState>("none");

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="full">
      <ModalContent p={2}>
        <ModalCloseButton />
        <Flex as={Box} gap={2} grow={1} h="full">
          <VStack
            w="25%"
            border="1px"
            borderColor="gray.200"
            borderRadius="sm"
            p={2}
            alignItems="start"
          >
            {modalState == "none" ? (
              <>
                <Button
                  rightIcon={<ArrowForwardIcon />}
                  onClick={() => setModalState("configure")}
                >
                  Configuration
                </Button>
                <Button
                  rightIcon={<ArrowForwardIcon />}
                  onClick={() => setModalState("style")}
                >
                  Style
                </Button>
              </>
            ) : null}
            {modalState == "configure" ? (
              <>
                <Button
                  leftIcon={<ArrowBackIcon />}
                  onClick={() => setModalState("none")}
                >
                  Back
                </Button>
                <Text>Configure screen (coming soon)</Text>
              </>
            ) : null}
            {modalState == "style" ? (
              <>
                <Button
                  leftIcon={<ArrowBackIcon />}
                  onClick={() => setModalState("none")}
                />
                <Text>Style screen (coming soon)</Text>
              </>
            ) : null}
          </VStack>
          <Flex
            p={2}
            w="75%"
            border="1px"
            borderColor="gray.200"
            borderRadius="sm"
          >
            test
          </Flex>
        </Flex>
      </ModalContent>
    </Modal>
  );
};

export default ConfigurePrivacyExperienceModal;
