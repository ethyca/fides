import { Input, InputGroup, InputLeftElement, Stack } from "@fidesui/react";
import React from "react";
import { useDispatch, useSelector } from "react-redux";

import { SearchLineIcon } from "../common/Icon";
import SystemTypeMenu from "./ConnectionDropdown";
import ConnectionStatusMenu from "./ConnectionStatusMenu";
import {
  selectDatastoreConnectionFilters,
  setDisabledStatus,
  setSearch,
  setSystemType,
  setTestingStatus,
} from "./datastore-connection.slice";
import { DisabledStatus, SystemType, TestingStatus } from "./types";

const useConstantFilters = () => {
  const filters = useSelector(selectDatastoreConnectionFilters);
  const dispatch = useDispatch();
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) =>
    dispatch(setSearch(event.target.value));
  const handleSystemTypeChange = (value: string) =>
    dispatch(setSystemType(value));
  const handleTestingStatusChange = (value: string) =>
    dispatch(setTestingStatus(value));
  const handleDisabledStatusChange = (value: string) =>
    dispatch(setDisabledStatus(value));

  return {
    handleSearchChange,
    handleSystemTypeChange,
    handleTestingStatusChange,
    handleDisabledStatusChange,
    ...filters,
  };
};

const ConnectionFilters: React.FC = () => {
  const {
    handleSearchChange,
    handleSystemTypeChange,
    handleTestingStatusChange,
    handleDisabledStatusChange,
    search,
    // eslint-disable-next-line @typescript-eslint/naming-convention
    system_type,
    // eslint-disable-next-line @typescript-eslint/naming-convention
    test_status,
    // eslint-disable-next-line @typescript-eslint/naming-convention
    disabled_status,
  } = useConstantFilters();
  return (
    <Stack direction="row" spacing={4} mb={6}>
      <InputGroup size="sm">
        <InputLeftElement pointerEvents="none">
          <SearchLineIcon color="gray.300" w="17px" h="17px" />
        </InputLeftElement>
        <Input
          type="search"
          minWidth={200}
          placeholder="Search"
          size="sm"
          borderRadius="md"
          value={search}
          name="search"
          onChange={handleSearchChange}
        />
      </InputGroup>
      <ConnectionStatusMenu />
      <SystemTypeMenu
        title="System Type"
        filterOptions={Object.values(SystemType)}
        value={system_type}
        setValue={handleSystemTypeChange}
      />
      <SystemTypeMenu
        title="Testing Status"
        filterOptions={Object.values(TestingStatus)}
        value={test_status}
        setValue={handleTestingStatusChange}
      />

      <SystemTypeMenu
        title="Status"
        filterOptions={Object.values(DisabledStatus)}
        value={disabled_status}
        setValue={handleDisabledStatusChange}
      />
    </Stack>
  );
};

export default ConnectionFilters;
