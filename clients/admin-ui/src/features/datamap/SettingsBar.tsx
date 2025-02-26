import {
  AntButton as Button,
  AntTag as Tag,
  Flex,
  Text,
  useDisclosure,
} from "fidesui";
import { uniq } from "lodash";
import React, { useContext, useMemo } from "react";

import { useFeatures } from "~/features/common/features";
import QuestionTooltip from "~/features/common/QuestionTooltip";
import { GlobalFilterV2 } from "~/features/common/table/v2";
import DatamapTableContext from "~/features/datamap/datamap-table/DatamapTableContext";
import FilterModal from "~/features/datamap/modals/FilterModal";

const useSettingsBar = () => {
  const {
    isOpen: isFilterModalOpen,
    onOpen: onFilterModalOpen,
    onClose: onFilterModalClose,
  } = useDisclosure();

  return {
    isFilterModalOpen,
    onFilterModalOpen,
    onFilterModalClose,
  };
};

const SettingsBar = () => {
  const { isFilterModalOpen, onFilterModalOpen, onFilterModalClose } =
    useSettingsBar();

  const { tableInstance } = useContext(DatamapTableContext);
  const { systemsCount: totalSystemsCount, dictionaryService: compassEnabled } =
    useFeatures();

  const rowModel = tableInstance?.getRowModel();
  const uniqueSystemKeysFromFilteredRows = useMemo(() => {
    const rows = rowModel?.rows || [];
    return uniq(rows?.map((row) => row.original["system.fides_key"]));
  }, [rowModel]);

  if (!tableInstance) {
    return null;
  }

  const filteredSystemsCount = uniqueSystemKeysFromFilteredRows.length;
  const totalFiltersApplied = tableInstance.getState().columnFilters.length;

  return (
    <>
      <Flex
        justifyContent="flex-end"
        flexDirection="row"
        alignItems="center"
        flexWrap="wrap"
        rowGap={4}
        columnGap={4}
      >
        <Flex flexGrow={1}>
          <GlobalFilterV2
            globalFilter={tableInstance.getState().globalFilter}
            setGlobalFilter={tableInstance.setGlobalFilter}
          />
        </Flex>
        <Flex>
          {totalSystemsCount > 0 ? (
            <Flex alignItems="center" borderRadius="md" gap={1} marginRight={4}>
              <Text fontSize="xs">
                {filteredSystemsCount} of {totalSystemsCount} systems displayed
              </Text>
              {compassEnabled ? (
                <QuestionTooltip label="Note that Global Vendor List (GVL) and Additional Consent (AC) systems are not currently included in these reports" />
              ) : null}
            </Flex>
          ) : null}
          <Button aria-label="Open Filter Settings" onClick={onFilterModalOpen}>
            Filter
            {totalFiltersApplied > 0 ? (
              <Tag className="ml-2">{totalFiltersApplied}</Tag>
            ) : null}
          </Button>
        </Flex>
      </Flex>
      <FilterModal isOpen={isFilterModalOpen} onClose={onFilterModalClose} />
    </>
  );
};

export default SettingsBar;
