import {
  Flex,
  Input,
  InputGroup,
  InputLeftElement,
  SearchLineIcon,
} from "fidesui";
import React from "react";
import { useDispatch, useSelector } from "react-redux";

import {
  selectDatastoreConnectionFilters,
  setSearch,
} from "./datastore-connection.slice";
import ConnectionTypeFilter from "./filters/ConnectionTypeFilter";
import DisabledStatusFilter from "./filters/DisabledStatusFilter";
import SystemTypeFilter from "./filters/SystemTypeFilter";
import TestingStatusFilter from "./filters/TestingStatusFilter";

const useConstantFilters = () => {
  const filters = useSelector(selectDatastoreConnectionFilters);
  const dispatch = useDispatch();
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) =>
    dispatch(setSearch(event.target.value));

  return {
    handleSearchChange,
    ...filters,
  };
};

const ConnectionFilters = () => {
  const { handleSearchChange, search } = useConstantFilters();
  return (
    <Flex
      minWidth="fit-content"
      alignItems="center"
      gap="4"
      mb={6}
      flexWrap="wrap"
    >
      <InputGroup size="sm" minWidth="308px">
        <InputLeftElement pointerEvents="none">
          <SearchLineIcon color="gray.300" w="17px" h="17px" />
        </InputLeftElement>
        <Input
          autoComplete="off"
          autoFocus
          type="search"
          minWidth={200}
          placeholder="Search connection name or description"
          size="sm"
          borderRadius="md"
          value={search}
          name="search"
          onChange={handleSearchChange}
        />
      </InputGroup>
      <ConnectionTypeFilter />
      <SystemTypeFilter />
      <TestingStatusFilter />
      <DisabledStatusFilter />
    </Flex>
  );
};

export default ConnectionFilters;
