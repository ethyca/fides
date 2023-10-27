import {
  Box,
  Button,
  Checkbox,
  Divider,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Text,
} from "@fidesui/react";
import { Table as TableInstance } from "@tanstack/react-table";
import React, { useMemo, useState } from "react";

type FilterCheckboxProps = {
  onChange: () => void;
  displayText: string;
  value: string;
  isChecked: boolean;
};

const FilterCheckbox = ({
  onChange,
  displayText,
  isChecked,
  value,
}: FilterCheckboxProps) => (
  <Checkbox
    value={value}
    key={value}
    height="20px"
    mb={3}
    isChecked={isChecked}
    onChange={onChange}
    colorScheme="complimentary"
    mr={5}
  >
    <Text
      fontSize="sm"
      lineHeight={5}
      height="20px"
      textOverflow="ellipsis"
      overflow="hidden"
      whiteSpace="nowrap"
    >
      {displayText}
    </Text>
  </Checkbox>
);

interface MultipleSystemsFilterProps<T> {
  tableInstance: TableInstance<T>;
  isOpen: boolean;
  onClose: () => void;
}

const initialFilterState = {
  gvl: false,
  gacp: false,
};

const MultipleSystemsFilter = <T,>({
  isOpen,
  onClose,
  tableInstance,
}: MultipleSystemsFilterProps<T>) => {
  const [filters, setFilters] = useState(initialFilterState);

  useMemo(() => {
    const columnFilters: {
      id: string;
      value: string[];
    } = {
      id: "vendor_id",
      value: [],
    };
    if (filters.gvl) {
      columnFilters.value.push("gvl");
    }

    if (filters.gacp) {
      columnFilters.value.push("gacp");
    }

    tableInstance.setColumnFilters([columnFilters]);
  }, [filters, tableInstance]);

  const resetFilters = () => {
    tableInstance.setColumnFilters([]);
    setFilters(initialFilterState);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} isCentered size="2xl">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>Filters</ModalHeader>
        <ModalCloseButton />
        <Divider />
        <ModalBody maxH="85vh" px={6} py={4} overflowX="auto">
          <Text fontSize="md" fontWeight="bold" mb={2}>
            Sources
          </Text>
          <FilterCheckbox
            onChange={() => {
              setFilters((prev) => ({ ...prev, gvl: !prev.gvl }));
            }}
            displayText="GVL"
            isChecked={filters.gvl}
            value="gvl"
          />
          <FilterCheckbox
            onChange={() => {
              setFilters((prev) => ({ ...prev, gacp: !prev.gacp }));
            }}
            displayText="AC"
            isChecked={filters.gacp}
            value="gacp"
          />
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
};

export default MultipleSystemsFilter;
