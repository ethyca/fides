import { Table as TableInstance } from "@tanstack/react-table";
import {
  AntButton,
  Box,
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
} from "fidesui";
import React, { useMemo, useState } from "react";

import { vendorSourceLabels, VendorSources } from "~/features/common/helpers";

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
    id={`checkbox-${value}`}
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

type FilterState = {
  [key in keyof typeof VendorSources]: boolean;
};
const initialFilterState: FilterState = {
  GVL: false,
  AC: false,
  COMPASS: false,
};

const MultipleSystemsFilterModal = <T,>({
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
    if (filters.GVL) {
      columnFilters.value.push("gvl");
    }

    if (filters.AC) {
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
              setFilters((prev) => ({ ...prev, GVL: !prev.GVL }));
            }}
            displayText={vendorSourceLabels.gvl.fullName}
            isChecked={filters.GVL}
            value="gvl"
          />
          <FilterCheckbox
            onChange={() => {
              setFilters((prev) => ({ ...prev, AC: !prev.AC }));
            }}
            displayText={vendorSourceLabels.gacp.fullName}
            isChecked={filters.AC}
            value="gacp"
          />
        </ModalBody>
        <ModalFooter>
          <Box display="flex" justifyContent="space-between" width="100%">
            <AntButton onClick={resetFilters} className="mr-3 grow">
              Reset Filters
            </AntButton>
            <AntButton
              data-testid="filter-done-btn"
              type="primary"
              onClick={onClose}
              className="grow"
            >
              Done
            </AntButton>
          </Box>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default MultipleSystemsFilterModal;
