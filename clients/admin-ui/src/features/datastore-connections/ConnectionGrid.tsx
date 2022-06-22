import { Button, Flex, SimpleGrid, Spinner, Text } from "@fidesui/react";
import debounce from "lodash.debounce";
import React, { useEffect, useRef, useState } from "react";
import { useDispatch } from "react-redux";

import { useAppSelector } from "../../app/hooks";
import PaginationFooter from "../common/PaginationFooter";
import ConnectionGridItem from "./ConnectionGridItem";
import {
  selectDatastoreConnectionFilters,
  setPage,
  useGetAllDatastoreConnectionsQuery,
} from "./datastore-connection.slice";

const useConnectionGrid = () => {
  const dispatch = useDispatch();
  const filters = useAppSelector(selectDatastoreConnectionFilters);
  const [cachedFilters, setCachedFilters] = useState(filters);
  const updateCachedFilters = useRef(
    debounce((updatedFilters) => setCachedFilters(updatedFilters), 250)
  );
  useEffect(() => {
    updateCachedFilters.current(filters);
  }, [setCachedFilters, filters]);

  const handlePreviousPage = () => {
    dispatch(setPage(filters.page - 1));
  };

  const handleNextPage = () => {
    dispatch(setPage(filters.page + 1));
  };

  const { data, isLoading, isUninitialized } =
    useGetAllDatastoreConnectionsQuery(cachedFilters);
  const { items: connections, total } = data || { items: [], total: 0 };
  return {
    ...filters,
    data,
    isLoading,
    isUninitialized,
    connections,
    total,
    handleNextPage,
    handlePreviousPage,
  };
};

const ConnectionGrid: React.FC = () => {
  const {
    data,
    isUninitialized,
    isLoading,
    page,
    size,
    total,
    handleNextPage,
    handlePreviousPage,
  } = useConnectionGrid();
  if (isUninitialized || isLoading) {
    return <Spinner />;
  }

  let body = (
    <Flex
      bg="gray.50"
      width="100%"
      height="340px"
      justifyContent="center"
      alignItems="center"
      flexDirection="column"
    >
      <Text
        color="black"
        fontSize="x-large"
        lineHeight="32px"
        fontWeight="600"
        mb="7px"
      >
        Welcome to your Datastore!
      </Text>
      <Text color="gray.600" fontSize="sm" lineHeight="20px" mb="11px">
        You don&lsquo;t have any Connections set up yet.
      </Text>
      <Button
        variant="solid"
        bg="primary.800"
        _hover={{ bg: "primary.800" }}
        color="white"
        flexShrink={0}
        size="sm"
        disabled
      >
        Create New Connection
      </Button>
    </Flex>
  );

  // @ts-ignore
  if (data?.items.length > 0) {
    const gridItems = data!.items.map((d) => (
      <ConnectionGridItem key={d.key} connectionData={d} />
    ));
    body = (
      <>
        <SimpleGrid minChildWidth={400}>{gridItems}</SimpleGrid>
        <PaginationFooter
          page={page}
          size={size}
          total={total}
          handleNextPage={handleNextPage}
          handlePreviousPage={handlePreviousPage}
        />
      </>
    );
  }

  return body;
};

export default ConnectionGrid;
