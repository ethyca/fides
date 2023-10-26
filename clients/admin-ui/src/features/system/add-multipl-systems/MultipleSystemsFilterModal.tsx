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
  Checkbox,
  Text,
} from "@fidesui/react";
import React, { ReactNode, useState, useMemo } from "react";
import { Table as TableInstance } from "@tanstack/react-table";

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
    width="193px"
    height="20px"
    mb="25px"
    isChecked={isChecked}
    onChange={onChange}
    _focusWithin={{
      bg: "gray.100",
    }}
    colorScheme="complimentary"
  >
    <Text
      fontSize="sm"
      lineHeight={5}
      height="20px"
      width="170px"
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

const MultipleSystemsFilter = <T,>({
  isOpen,
  onClose,
  tableInstance,
}: MultipleSystemsFilterProps<T>) => {
  const anyFiltersActive = tableInstance.getState().columnFilters.length > 0;
  const [filters, setFilters] = useState({
    gvl: false,
    gacp: false,
  });


  useMemo(()=>{
    const columnFilters= {
      id: "vendor_id",
      value: []
    }
    if(filters.gvl){
      columnFilters.value.push("gvl")  
    }

    if(filters.gacp){
      columnFilters.value.push("gacp")  
    }
    console.log(columnFilters)
    
    tableInstance.setColumnFilters([columnFilters])

    
  },[filters])

  
  const resetFilters = () => {
    tableInstance.setColumnFilters([]);
    setFilters({
      gvl: false,
      gacp: false,
    })
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} isCentered size="2xl">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>Filters</ModalHeader>
        <ModalCloseButton />
        <Divider />
        <ModalBody maxH="85vh" padding="0px" overflowX="auto">
          <Heading height="56px">
            <Box
              flex="1"
              alignItems="center"
              justifyContent="center"
              textAlign="left"
            >
              Sources
            </Box>
          </Heading>
          <FilterCheckbox
            onChange={() => {
              setFilters((prev) => {
                return { ...prev, gvl: !prev.gvl };
              });
            }}
            displayText="GVL"
            isChecked={filters["gvl"]}
            value="gvl"
          />
          <FilterCheckbox
            onChange={() => {
              setFilters((prev) => {
                return { ...prev, gacp: !prev.gacp };
              });
            }}
            displayText="AC"
            isChecked={filters["gacp"]}
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
