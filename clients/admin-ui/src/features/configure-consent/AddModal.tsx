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

const AddModal = ({
  title,
  children,
  isOpen,
  onClose,
  onSuggestionClick,
}: Pick<UseDisclosureReturn, "isOpen" | "onClose"> & {
  title: string;
  children: ReactNode;
  onSuggestionClick: () => void;
}) => {
  const features = useFeatures();

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      isCentered
      scrollBehavior="inside"
      size="3xl"
    >
      <ModalOverlay />
      <ModalContent textAlign="left" p={0}>
        <ModalHeader p={0}>
          <Box
            px={6}
            py={4}
            display="flex"
            justifyContent="space-between"
            alignItems="center"
          >
            <Heading as="h3" size="sm">
              {title}
            </Heading>
            {features.dictionaryService ? (
              <IconButton
                icon={<SparkleIcon />}
                aria-label="See compass suggestions"
                variant="outline"
                borderColor="gray.200"
                onClick={onSuggestionClick}
              />
            ) : null}
          </Box>
        </ModalHeader>
        <ModalBody pb={4}>{children}</ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default AddModal;
