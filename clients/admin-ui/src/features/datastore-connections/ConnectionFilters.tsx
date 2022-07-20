import { Input, InputGroup, InputLeftElement, Stack } from "@fidesui/react";
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
      <ConnectionTypeFilter />
      <SystemTypeFilter />
      <TestingStatusFilter />
      <DisabledStatusFilter />
    </Stack>
  );
};

export default ConnectionFilters;
