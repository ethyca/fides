import { Box, Spinner, Text } from "@fidesui/react";
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

    return data.items.filter((s) => SEARCH_FILTER(s, searchFilter));
  }, [data, searchFilter]);

  if (isLoading) {
    return <Spinner />;
  }

  if (!data) {
    return <Text>Could not find system types, please try again.</Text>;
  }

  return (
    <Box>
      <Box maxWidth="30vw" mb={4}>
        <SearchBar
          search={searchFilter}
          onChange={setSearchFilter}
          placeholder="Search for a system"
          data-testid="system-catalog-search"
          withClear
        />
      </Box>
      <ConnectionTypeList items={filteredConnections} />
    </Box>
  );
};

export default SystemCatalog;
