import {
  Box,
  Button,
  Flex,
  SearchLineIcon,
  Spinner,
  Text,
} from "@fidesui/react";
import NextLink from "next/link";
import { useMemo, useState } from "react";

import SearchBar from "~/features/common/SearchBar";
import { useGetAllConnectionTypesQuery } from "~/features/connection-type";
import ConnectionTypeList from "~/features/datastore-connections/add-connection/ConnectionTypeList";
import { ConnectionSystemTypeMap } from "~/types/api";

const SEARCH_FILTER = (connection: ConnectionSystemTypeMap, search: string) =>
  connection.human_readable
    .toLocaleLowerCase()
    .includes(search.toLocaleLowerCase()) ||
  connection.identifier
    .toLocaleLowerCase()
    .includes(search.toLocaleLowerCase());

const SystemCatalog = () => {
  const [searchFilter, setSearchFilter] = useState("");
  const { data, isLoading } = useGetAllConnectionTypesQuery({});
  const filteredConnections = useMemo(() => {
    if (!data) {
      return [];
    }

    return data.items.filter((i) => SEARCH_FILTER(i, searchFilter));
  }, [data, searchFilter]);

  if (isLoading) {
    return <Spinner />;
  }

  if (!data) {
    return <Text>Could not find system types, please try again.</Text>;
  }

  const noSearchResults =
    data.items.length > 0 &&
    searchFilter.length > 0 &&
    filteredConnections.length === 0;

  return (
    <Box>
      <Box mb={4} display="flex" justifyContent="space-between">
        <Box>
          <SearchBar
            search={searchFilter}
            onChange={setSearchFilter}
            placeholder="Search for a system"
            data-testid="system-catalog-search"
            withClear
          />
        </Box>
        <Flex alignItems="center">
          {noSearchResults ? (
            <>
              <SearchLineIcon mr={1} color="gray.400" />
              <Text
                fontSize="sm"
                color="gray.700"
                mr={2}
                data-testid="no-systems-found"
              >
                No systems found
              </Text>
            </>
          ) : null}
          <NextLink
            href={{
              pathname: window.location.pathname,
              query: { step: 2 },
            }}
            passHref
          >
            <Button
              variant={noSearchResults ? "solid" : "outline"}
              colorScheme={noSearchResults ? "primary" : undefined}
              size="sm"
              data-testid="create-system-btn"
            >
              Create system
            </Button>
          </NextLink>
        </Flex>
      </Box>
      <ConnectionTypeList items={filteredConnections} />
    </Box>
  );
};

export default SystemCatalog;
