import {
  Box,
  Heading,
  IconButton,
  Modal,
  ModalBody,
  ModalContent,
  ModalHeader,
  ModalOverlay,
  UseDisclosureReturn,
} from "@fidesui/react";
import { ReactNode } from "react";

import { useFeatures } from "~/features/common/features";
import { SparkleIcon } from "~/features/common/Icon/SparkleIcon";

type SuggestionsState = "showing" | "disabled";

const AddModal = ({
  title,
  children,
  isOpen,
  onClose,
  onSuggestionClick,
  suggestionsState,
}: Pick<UseDisclosureReturn, "isOpen" | "onClose"> & {
  title: string;
  children: ReactNode;
  onSuggestionClick: () => void;
  suggestionsState?: SuggestionsState;
}) => {
  const features = useFeatures();

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      isCentered
      scrollBehavior="inside"
      size="xl"
    >
      <ModalOverlay />
      <ModalContent textAlign="left" p={0}>
        <ModalHeader p={0}>
          <Box
            backgroundColor="gray.50"
            px={6}
            py={4}
            border="1px"
            borderColor="gray.200"
            borderTopRadius={6}
            display="flex"
            justifyContent="space-between"
            alignItems="center"
          >
            <Heading as="h3" size="sm">
              {title}
            </Heading>
            {features.dictionaryService ? (
              <IconButton
                icon={
                  <SparkleIcon
                    color={
                      suggestionsState === "showing"
                        ? "complimentary.500"
                        : undefined
                    }
                  />
                }
                aria-label="See compass suggestions"
                variant="outline"
                borderColor="gray.200"
                onClick={onSuggestionClick}
                isDisabled={suggestionsState === "disabled"}
                data-testid="sparkle-btn"
              />
            ) : null}
          </Box>
        </ModalHeader>
        <ModalBody pb={4} overflow="scroll">
          {children}
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default AddModal;
