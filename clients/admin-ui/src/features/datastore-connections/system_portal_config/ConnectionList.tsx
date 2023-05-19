import {
  Box,
  Button,
  Center,
  Flex,
  Input,
  InputGroup,
  InputLeftElement,
  SearchLineIcon,
  Spinner,
  Text,
  SimpleGrid,
  Select
} from "@fidesui/react";
import { debounce } from "common/utils";
import {
  selectConnectionTypeFilters,
  selectConnectionTypeState,
  setSearch,
  useGetAllConnectionTypesQuery,
} from "connection-type/connection-type.slice";
import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useDispatch } from "react-redux";

import { useAppSelector } from "~/app/hooks";
import Restrict from "~/features/common/Restrict";
import ConnectorTemplateUploadModal from "~/features/connector-templates/ConnectorTemplateUploadModal";
import { ConnectionSystemTypeMap, ScopeRegistryEnum } from "~/types/api";

import Breadcrumb from "../add-connection/Breadcrumb";
import ConnectionTypeFilter from "../add-connection/ConnectionTypeFilter";
import ConnectionTypeList from "../add-connection/ConnectionTypeList";
import ConnectionTypeLogo from "datastore-connections/ConnectionTypeLogo";
import { CustomSelect, Option } from "~/features/common/form/inputs";
import { ConnectionOption } from "datastore-connections/system_portal_config/ConnectionForm";
import SelectDropdown from "~/features/common/dropdown/SelectDropdown"

type ItemProps = {
  data: ConnectionSystemTypeMap;
};
const ConnectinListItem = ({ data }: ItemProps) => {
  return (
    <Box
      boxShadow="base"
      borderRadius="5px"
      maxWidth="331px"
      overflow="hidden"
      _hover={{
        boxShadow: "lg",
        cursor: "pointer",
      }}
      data-testid={`${data.identifier}-item`}
    >
      <Flex alignItems="center" justifyContent="start" pl="24px" h="25px">
        <ConnectionTypeLogo data={data} />
        <Text
          marginLeft="12px"
          color="gray.700"
          fontSize="sm"
          fontStyle="normal"
          fontWeight="600"
        >
          {data.human_readable}
        </Text>
      </Flex>
    </Box>
  );
};

type ListProps = {
  onChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
};
const ConnectionList = ({ onChange }: ListProps) => {
  const dispatch = useDispatch();
  const filters = useAppSelector(selectConnectionTypeFilters);
  const { data, isFetching, isLoading, isSuccess } =
    useGetAllConnectionTypesQuery(filters);

  const handleSearchChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      if (event.target.value.length === 0 || event.target.value.length > 1) {
        dispatch(setSearch(event.target.value));
      }
    },
    [dispatch]
  );

  const debounceHandleSearchChange = useMemo(
    () => debounce(handleSearchChange, 250),
    [handleSearchChange]
  );

  const sortedItems = useMemo(
    () =>
      data?.items &&
      [...data.items].sort((a, b) =>
        a.human_readable > b.human_readable ? 1 : -1
      ),
    [data]
  );

  const dropDownOptions = useMemo(
    () =>
      sortedItems
        ? sortedItems.map((item) => ({
              label: item.human_readable,
              value: item

          }))
        : [],
    [sortedItems]
  );

  return (
    <>
      <Flex alignItems="center" gap="4" mb="24px" minWidth="fit-content">
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
            onChange={debounceHandleSearchChange}
            placeholder="Search Integrations"
            size="sm"
            type="search"
          />
        </InputGroup>
      </Flex>
      {(isFetching || isLoading) && (
        <Center>
          <Spinner />
        </Center>
      )}
      {isSuccess && sortedItems ? (
        <Select onChange={onChange} >
          {dropDownOptions.map((item)=>(
            <option key={item.label} value={JSON.stringify(item.value)}>{item.label}</option>
          ))}
        </Select>
      ) : null}
    </>
  );
};

export default ConnectionList;
