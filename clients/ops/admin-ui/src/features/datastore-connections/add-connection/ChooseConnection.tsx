import {
  Box,
  Center,
  Flex,
  Input,
  InputGroup,
  InputLeftElement,
  Spinner,
} from "@fidesui/react";
import { SearchLineIcon } from "common/Icon";
import { debounce } from "common/utils";
import React, { useEffect, useRef, useState } from "react";
import { useDispatch } from "react-redux";

import { useAppSelector } from "../../../app/hooks";
import {
  selectConnectionTypeFilters,
  setSearch,
  useGetAllConnectionTypesQuery,
} from "../../connection-type";
import { ConnectionTypeParams } from "../../connection-type/types";
import ConnectionTypeFilter from "./ConnectionTypeFilter";
import ConnectionTypeList from "./ConnectionTypeList";
import { AddConnectionStep } from "./types";

type ChooseConnectionProps = {
  currentStep: AddConnectionStep;
};

const ChooseConnection: React.FC<ChooseConnectionProps> = ({ currentStep }) => {
  const dispatch = useDispatch();
  const filters = useAppSelector(selectConnectionTypeFilters);
  const [cachedFilters, setCachedFilters] = useState(filters);
  const updateCachedFilters = useRef(
    debounce(
      (updatedFilters: React.SetStateAction<ConnectionTypeParams>) =>
        setCachedFilters(updatedFilters),
      250
    )
  );

  useEffect(() => {
    updateCachedFilters.current(filters);
  }, [setCachedFilters, filters]);

  const { data, isFetching, isLoading, isSuccess } =
    useGetAllConnectionTypesQuery(cachedFilters);

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) =>
    dispatch(setSearch(event.target.value));

  return (
    <>
      <Flex minWidth="max-content">
        <Box color="gray.700" fontSize="14px" maxHeight="80px" maxWidth="474px">
          {currentStep.description}
        </Box>
      </Flex>
      <Flex
        alignItems="center"
        gap="4"
        mb="24px"
        mt="24px"
        minWidth="max-content"
      >
        <ConnectionTypeFilter />
        <InputGroup size="sm">
          <InputLeftElement pointerEvents="none">
            <SearchLineIcon color="gray.300" h="17px" w="17px" />
          </InputLeftElement>
          <Input
            autoComplete="off"
            autoFocus
            borderRadius="md"
            name="search"
            onChange={handleSearchChange}
            placeholder="Search Integrations"
            size="sm"
            type="search"
            value={filters.search}
          />
        </InputGroup>
      </Flex>
      {(isFetching || isLoading) && (
        <Center>
          <Spinner />
        </Center>
      )}
      {isSuccess && data ? (
        <ConnectionTypeList
          items={[...data].sort((a, b) =>
            a.identifier > b.identifier ? 1 : -1
          )}
        />
      ) : null}
    </>
  );
};

export default ChooseConnection;
