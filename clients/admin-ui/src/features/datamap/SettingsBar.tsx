import {
  Button,
  FilterLightIcon,
  Flex,
  IconButton,
  Tag,
  Text,
  useDisclosure,
} from "fidesui";
import React, { useContext } from "react";

import { useFeatures } from "~/features/common/features";
import { GearLightIcon } from "~/features/common/Icon";
import QuestionTooltip from "~/features/common/QuestionTooltip";
import DatamapTableContext from "~/features/datamap/datamap-table/DatamapTableContext";
import GlobalFilter from "~/features/datamap/datamap-table/filters/global-accordion-filter/global-accordion-filter";
import FilterModal from "~/features/datamap/modals/FilterModal";
import SettingsModal from "~/features/datamap/modals/SettingsModal";

const useSettingsBar = () => {
  const {
    isOpen: isSettingsModalOpen,
    onOpen: onSettingsModalOpen,
    onClose: onSettingsModalClose,
  } = useDisclosure();

  const {
    isOpen: isFilterModalOpen,
    onOpen: onFilterModalOpen,
    onClose: onFilterModalClose,
  } = useDisclosure();

  return {
    isSettingsModalOpen,
    isFilterModalOpen,
    onSettingsModalOpen,
    onSettingsModalClose,
    onFilterModalOpen,
    onFilterModalClose,
  };
};

const SettingsBar: React.FC = () => {
  const {
    isFilterModalOpen,
    isSettingsModalOpen,
    onSettingsModalOpen,
    onSettingsModalClose,
    onFilterModalOpen,
    onFilterModalClose,
  } = useSettingsBar();

  const { tableInstance } = useContext(DatamapTableContext);
  const { systemsCount: totalSystemsCount, dictionaryService: compassEnabled } =
    useFeatures();
  if (!tableInstance) {
    return null;
  }

  const filteredSystemsCount = tableInstance.rows?.length || 0;
  const totalFiltersApplied = tableInstance?.state.filters
    .map<boolean[]>((f) => Object.values(f.value))
    .flatMap((f) => f)
    .filter((f) => f === true).length;

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
          <GlobalFilter
            globalFilter={tableInstance.state.globalFilter}
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
          <Button
            aria-label="Open Filter Settings"
            variant="solid"
            backgroundColor="#824EF2"
            color="white"
            size="sm"
            marginRight={4}
            onClick={onFilterModalOpen}
            _hover={{ opacity: 0.8 }}
            _active={{
              opacity: 0.8,
            }}
            rightIcon={<FilterLightIcon />}
          >
            Filter
            {totalFiltersApplied > 0 ? (
              <Tag
                ml={2}
                backgroundColor="complimentary.800"
                borderRadius="full"
                color="white"
              >
                {totalFiltersApplied}
              </Tag>
            ) : null}
          </Button>
          <IconButton
            aria-label="Open Column Settings"
            variant="ghost"
            size="sm"
            marginRight={1}
            onClick={onSettingsModalOpen}
            icon={<GearLightIcon />}
          />
        </Flex>
      </Flex>
      <FilterModal isOpen={isFilterModalOpen} onClose={onFilterModalClose} />
      <SettingsModal
        isOpen={isSettingsModalOpen}
        onClose={onSettingsModalClose}
      />
    </>
  );
};

export default SettingsBar;
