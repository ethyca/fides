import {
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  Button,
  Checkbox,
  Divider,
  Heading,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  SimpleGrid,
  Text,
} from "@fidesui/react";
import React, { ReactNode, useState } from "react";

export const getQueryParamsFromList = (
  optionList: Option[],
  queryParam: string
) => {
  const checkedOptions = optionList.filter((option) => option.isChecked);
  return checkedOptions.length > 0
    ? `${queryParam}=${checkedOptions
        .map((option) => option.value)
        .join(`&${queryParam}=`)}`
    : undefined;
};

export type Option = {
  value: string;
  displayText: string;
  isChecked: boolean;
};
type AccordionMultiFieldCheckBoxProps = {
  value: string;
  displayText: string;
  isChecked: boolean;
  onCheckboxChange: (fidesKey: string, checked: boolean) => void;
};

const AccordionMultiFieldCheckBox = ({
  value,
  displayText,
  isChecked,
  onCheckboxChange,
}: AccordionMultiFieldCheckBoxProps) => (
  <Checkbox
    value={value}
    key={value}
    height="20px"
    mb="25px"
    isChecked={isChecked}
    onChange={({ target }) => {
      onCheckboxChange(value, (target as HTMLInputElement).checked);
    }}
    _focusWithin={{
      bg: "gray.100",
    }}
    colorScheme="complimentary"
  >
    <Text
      fontSize="sm"
      lineHeight={5}
      textOverflow="ellipsis"
      overflow="hidden"
    >
      {displayText}
    </Text>
  </Checkbox>
);

type AccordionMultiFieldProps = {
  options: Option[];
  header: string;
  onCheckboxChange: (newValue: string, checked: boolean) => void;
  columns?: number;
  numDefaultOptions?: number;
};

export const AccordionMultifieldFilter = ({
  options,
  header,
  onCheckboxChange,
  columns = 3,
  numDefaultOptions = 15,
}: AccordionMultiFieldProps) => {
  const [isViewingMore, setIsViewingMore] = useState(false);
  const viewableOptions = isViewingMore
    ? options
    : options.slice(0, numDefaultOptions);
  const areExtraOptionsAvailable = options.length > numDefaultOptions;

  return (
    <AccordionItem border="0px" padding="12px 8px 8px 12px">
      <Heading height="56px">
        <AccordionButton height="100%">
          <Box
            flex="1"
            alignItems="center"
            justifyContent="center"
            textAlign="left"
            fontWeight={600}
          >
            {header}
          </Box>
          <AccordionIcon />
        </AccordionButton>
      </Heading>
      <AccordionPanel id={`panel-${header}`}>
        <SimpleGrid columns={columns}>
          {viewableOptions.map((option) => (
            <AccordionMultiFieldCheckBox
              key={option.value}
              {...option}
              onCheckboxChange={onCheckboxChange}
            />
          ))}
        </SimpleGrid>
        {!isViewingMore && areExtraOptionsAvailable ? (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              setIsViewingMore(true);
            }}
          >
            View more
          </Button>
        ) : null}
        {isViewingMore && areExtraOptionsAvailable ? (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              setIsViewingMore(false);
            }}
          >
            View less
          </Button>
        ) : null}
      </AccordionPanel>
    </AccordionItem>
  );
};

export default AccordionMultifieldFilter;

type FilterSectionProps = {
  heading?: string;
  children: ReactNode;
};

export const FilterSection = ({ heading, children }: FilterSectionProps) => (
  <Box padding="12px 8px 8px 12px" maxHeight={600}>
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
      <ModalBody
        maxH="85vh"
        padding="0px"
        overflowX="auto"
        style={{ scrollbarGutter: "stable" }}
      >
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
            Reset filters
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
