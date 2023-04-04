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
} from '@fidesui/react';
import React, { ReactNode, useContext, useMemo } from 'react';
import { HeaderGroup } from 'react-table';

import { DatamapRow } from '~/features/datamap';
import {
  DATA_CATEGORY_COLUMN_ID,
  SYSTEM_DATA_RESPONSIBILITY_TITLE,
  SYSTEM_PRIVACY_DECLARATION_DATA_SUBJECTS_NAME,
  SYSTEM_PRIVACY_DECLARATION_DATA_USE_NAME,
} from '~/features/datamap/constants';
import DatamapTableContext from '~/features/datamap/datamap-table/DatamapTableContext';

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

const FilterModal: React.FC<FilterModalProps> = ({ isOpen, onClose }) => {
  const { tableInstance } = useContext(DatamapTableContext);

  const { headerGroups } = useMemo(
    () => tableInstance || { headerGroups: [] },
    [tableInstance]
  );

  const getHeaderFilter = (
    headers: HeaderGroup<DatamapRow>[],
    columnId: string
  ): ReactNode =>
    headers
      .filter((column) => column.id === columnId)
      .map((column) =>
        column.render('Filter', {
          key: column.id,
        })
      );

  const anyFiltersActive = (
    headers: HeaderGroup<DatamapRow>[],
    columnIds: string[]
  ): boolean => headers.some((column) => columnIds.indexOf(column.id) > -1);

  const headers = useMemo(
    () =>
      headerGroups.length > 0
        ? headerGroups[0].headers.map((group) => group)
        : [],
    [headerGroups]
  );

  const resetFilters = () => {
    tableInstance?.setAllFilters([]);
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
              {getHeaderFilter(
                headers,
                SYSTEM_PRIVACY_DECLARATION_DATA_USE_NAME
              )}
              {getHeaderFilter(headers, DATA_CATEGORY_COLUMN_ID)}
              {getHeaderFilter(
                headers,
                SYSTEM_PRIVACY_DECLARATION_DATA_SUBJECTS_NAME
              )}
            </FilterSection>
          ) : null}
          {anyFiltersActive(headers, [SYSTEM_DATA_RESPONSIBILITY_TITLE]) ? (
            <>
              <Divider />
              <FilterSection heading="Responsibility">
                {getHeaderFilter(headers, SYSTEM_DATA_RESPONSIBILITY_TITLE)}
              </FilterSection>
            </>
          ) : null}
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

export default FilterModal;
