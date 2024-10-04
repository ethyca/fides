import { Header } from "@tanstack/react-table";
import {
  AntButton,
  Box,
  Divider,
  Heading,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
} from "fidesui";
import React, { ReactNode, useContext, useMemo } from "react";

import { DatamapRow } from "~/features/datamap";
import {
  DATA_CATEGORY_COLUMN_ID,
  SYSTEM_PRIVACY_DECLARATION_DATA_SUBJECTS_NAME,
  SYSTEM_PRIVACY_DECLARATION_DATA_USE_NAME,
} from "~/features/datamap/constants";
import DatamapTableContext from "~/features/datamap/datamap-table/DatamapTableContext";
import AccordionMultifieldFilter from "~/features/datamap/datamap-table/filters/accordion-multifield-filter/AccordionMultifieldFilter";

type FilterSectionProps = {
  heading: string;
  children: ReactNode;
};

const FilterSection = ({ heading, children }: FilterSectionProps) => (
  <Box padding="24px 8px 8px 24px">
    <Heading size="md" lineHeight={6} fontWeight="bold" mb={2}>
      {heading}
    </Heading>
    {children}
  </Box>
);

interface FilterModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const FilterModal = ({ isOpen, onClose }: FilterModalProps) => {
  const { tableInstance } = useContext(DatamapTableContext);

  const headerGroups = tableInstance?.getHeaderGroups();

  const renderHeaderFilter = (
    headers: Header<DatamapRow, unknown>[],
    columnId: string,
  ): ReactNode =>
    headers
      .filter((header) => header.id === columnId)
      .map((header) => (
        <AccordionMultifieldFilter column={header.column} key={columnId} />
      ));

  const anyFiltersActive = (
    headers: Header<DatamapRow, unknown>[],
    columnIds: string[],
  ): boolean => headers.some((column) => columnIds.indexOf(column.id) > -1);

  const headers = useMemo(
    () => headerGroups?.[0].headers || [],
    [headerGroups],
  );

  const resetFilters = () => {
    tableInstance?.resetColumnFilters();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} isCentered size="2xl">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>Filters</ModalHeader>
        <ModalCloseButton />
        <Divider />
        <ModalBody maxH="85vh" padding="0px" overflowX="auto">
          {anyFiltersActive(headers, [
            SYSTEM_PRIVACY_DECLARATION_DATA_USE_NAME,
            DATA_CATEGORY_COLUMN_ID,
            SYSTEM_PRIVACY_DECLARATION_DATA_SUBJECTS_NAME,
          ]) ? (
            <FilterSection heading="Privacy attributes">
              {renderHeaderFilter(
                headers,
                SYSTEM_PRIVACY_DECLARATION_DATA_USE_NAME,
              )}
              {renderHeaderFilter(headers, DATA_CATEGORY_COLUMN_ID)}
              {renderHeaderFilter(
                headers,
                SYSTEM_PRIVACY_DECLARATION_DATA_SUBJECTS_NAME,
              )}
            </FilterSection>
          ) : null}
        </ModalBody>
        <ModalFooter>
          <Box display="flex" justifyContent="space-between" width="100%">
            <AntButton onClick={resetFilters} className="mr-3 grow">
              Reset Filters
            </AntButton>
            <AntButton onClick={onClose} type="primary" className="grow">
              Done
            </AntButton>
          </Box>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default FilterModal;
