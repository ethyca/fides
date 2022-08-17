import { Flex, Input, InputGroup, InputLeftElement } from "@fidesui/react";
import React from "react";
import { useDispatch, useSelector } from "react-redux";

import { SearchLineIcon } from "../common/Icon";
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

const ConnectionFilters: React.FC = () => {
  const { handleSearchChange, search } = useConstantFilters();
  return (
    <Flex minWidth="max-content" alignItems="center" gap="4" mb={6}>
      <InputGroup size="sm" minWidth="308px">
        <InputLeftElement pointerEvents="none">
          <SearchLineIcon color="gray.300" w="17px" h="17px" />
        </InputLeftElement>
        <Input
          autoComplete="off"
          autoFocus
          type="search"
          minWidth={200}
          placeholder="Search datastore name or description"
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
