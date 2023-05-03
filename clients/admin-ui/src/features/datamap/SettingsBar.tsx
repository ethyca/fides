import {
  Button,
  ButtonGroup,
  FilterLightIcon,
  Flex,
  IconButton,
  Menu,
  MenuButton,
  Tag,
  useDisclosure,
} from "@fidesui/react";
import { baseApi } from "common/api.slice";
import React, { useContext, useEffect } from "react";
import { useDispatch } from "react-redux";

import { useAppSelector } from "~/app/hooks";
import { DownloadLightIcon, GearLightIcon } from "~/features/common/Icon";
import { selectIsMapOpen, setView } from "~/features/datamap/datamap.slice";
import DatamapTableContext from "~/features/datamap/datamap-table/DatamapTableContext";
import GlobalFilter from "~/features/datamap/datamap-table/filters/global-accordion-filter/global-accordion-filter";
import ExportModal from "~/features/datamap/modals/ExportModal";
import FilterModal from "~/features/datamap/modals/FilterModal";
import SettingsModal from "~/features/datamap/modals/SettingsModal";

const useSettingsBar = () => {
  const isMapOpen = useAppSelector(selectIsMapOpen);

  const {
    isOpen: isExportModalOpen,
    onOpen: onExportModalOpen,
    onClose: onExportModalClose,
  } = useDisclosure();

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

  const onExportClick = () => {
    onExportModalOpen();
  };

  return {
    isExportModalOpen,
    isMapOpen,
    isSettingsModalOpen,
    isFilterModalOpen,
    onSettingsModalOpen,
    onSettingsModalClose,
    onFilterModalOpen,
    onFilterModalClose,
    onExportClick,
    onExportModalClose,
    onExportModalOpen,
  };
};

const SettingsBar: React.FC = () => {
  const dispatch = useDispatch();
  const {
    isExportModalOpen,
    isFilterModalOpen,
    isSettingsModalOpen,
    onSettingsModalOpen,
    onSettingsModalClose,
    onFilterModalOpen,
    onFilterModalClose,
    onExportClick,
    onExportModalClose,
    isMapOpen,
  } = useSettingsBar();

  const { tableInstance } = useContext(DatamapTableContext);

  useEffect(() => {
    /*
    The tag needs to be invalided this way because the plusApi
    is not a part of the baseApi yet. This will be done on the
    API in the future.
     */
    dispatch(baseApi.util.invalidateTags(["Datamap"]));
  }, [dispatch, tableInstance]);

  if (!tableInstance) {
    return null;
  }

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
          <ButtonGroup isAttached size="sm" marginRight={4}>
            <Button
              colorScheme={isMapOpen ? "primary" : undefined}
              onClick={() => {
                dispatch(setView("map"));
              }}
              data-testid="map-btn"
            >
              Map
            </Button>
            <Button
              colorScheme={!isMapOpen ? "primary" : undefined}
              onClick={() => {
                dispatch(setView("table"));
              }}
              data-testid="table-btn"
            >
              Table
            </Button>
          </ButtonGroup>
          <IconButton
            aria-label="Open Column Settings"
            variant="ghost"
            size="sm"
            marginRight={1}
            onClick={onSettingsModalOpen}
            icon={<GearLightIcon />}
          />
          <Menu>
            <MenuButton
              as={IconButton}
              aria-label="Export data"
              icon={<DownloadLightIcon />}
              onClick={onExportClick}
              size="sm"
              variant="ghost"
            />
          </Menu>
        </Flex>
      </Flex>
      <FilterModal isOpen={isFilterModalOpen} onClose={onFilterModalClose} />
      <ExportModal isOpen={isExportModalOpen} onClose={onExportModalClose} />
      <SettingsModal
        isOpen={isSettingsModalOpen}
        onClose={onSettingsModalClose}
      />
    </>
  );
};

export default SettingsBar;
