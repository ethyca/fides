import {
  Box,
  Button,
  Divider,
  Heading,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
} from "@fidesui/react";
import React, { ReactNode } from "react";

type FilterSectionProps = {
  heading?: string;
  children: ReactNode;
};

export const FilterSection = ({ heading, children }: FilterSectionProps) => (
  <Box padding="24px 8px 8px 24px">
    {heading ? (
      <Heading size="md" lineHeight={6} fontWeight="bold" mb={2}>
        {heading}
      </Heading>
    ) : null}
    {children}
  </Box>
);

interface FilterModalProps {
  isOpen: boolean;
  onClose: () => void;
  resetFilters: () => void;
}

export const FilterModal: React.FC<FilterModalProps> = ({
  isOpen,
  onClose,
  children,
  resetFilters,
}) => (
  <Modal isOpen={isOpen} onClose={onClose} isCentered size="2xl">
    <ModalOverlay />
    <ModalContent>
      <ModalHeader>Filters</ModalHeader>
      <ModalCloseButton />
      <Divider />
      <ModalBody maxH="85vh" padding="0px" overflowX="auto">
        {children}
      </ModalBody>
      <ModalFooter>
        <Box display="flex" justifyContent="space-between" width="100%">
          <Button
            variant="outline"
            size="sm"
            mr={3}
            onClick={resetFilters}
            flexGrow={1}
          >
            Reset Filters
          </Button>
          <Button
            colorScheme="primary"
            size="sm"
            onClick={onClose}
            flexGrow={1}
          >
            Done
          </Button>
        </Box>
      </ModalFooter>
    </ModalContent>
  </Modal>
);
