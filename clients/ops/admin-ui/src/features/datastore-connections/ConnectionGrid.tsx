import { chunk } from "@chakra-ui/utils";
import {
  Box,
  Button,
  Center,
  Flex,
  SimpleGrid,
  Spinner,
  Text,
} from "@fidesui/react";
import debounce from "lodash.debounce";
import React, { useEffect, useRef, useState } from "react";
import { useDispatch } from "react-redux";

import { useAppSelector } from "../../app/hooks";
import PaginationFooter from "../common/PaginationFooter";
import classes from "./ConnectionGrid.module.css";
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

  const { data, isLoading, isUninitialized, isFetching, isSuccess } =
    useGetAllDatastoreConnectionsQuery(cachedFilters);
  // The result of the initial request data is being cached due to an issue with
  // RTK query. Not doing this will result in the welcome screen being showed
  // when it shouldn't sometimes
  const isInitialDataEmpty = useRef<boolean | undefined>(undefined);
  useEffect(() => {
    if (isInitialDataEmpty.current === undefined && isSuccess) {
      isInitialDataEmpty.current =
        !filters.search &&
        !filters.test_status &&
        !filters.disabled_status &&
        !filters.connection_type &&
        !filters.system_type &&
        data!.items.length === 0;
    }
  }, [data, filters, isSuccess]);
  return {
    ...filters,
    isInitialRenderEmpty: isInitialDataEmpty,
    data,
    isLoading,
    isUninitialized,
    isFetching,
    handleNextPage,
    handlePreviousPage,
  };
};

const ConnectionGrid: React.FC = () => {
  const {
    data,
    isUninitialized,
    isLoading,
    isFetching,
    isInitialRenderEmpty,
    page,
    size,
    handleNextPage,
    handlePreviousPage,
  } = useConnectionGrid();

  if (isUninitialized || isLoading || isFetching) {
    return (
      <Center>
        <Spinner />
      </Center>
    );
  }

  if (isInitialRenderEmpty.current) {
    return (
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
  }

  const columns = 3;
  const chunks = chunk(data!?.items, columns);

  return (
    <>
      {chunks.map((parent, index, { length }) => (
        <Box
          key={JSON.stringify(parent)}
          className={classes["grid-row"]}
          // Add bottom border only if last row is complete and there is more than 1 row rendered
          borderBottomWidth={
            length > 1 && index === length - 1 && parent.length === columns
              ? "0.5px"
              : undefined
          }
        >
          <SimpleGrid columns={columns}>
            {parent.map((child) => (
              <Box key={child.key} className={classes["grid-item"]}>
                <ConnectionGridItem connectionData={child} />
              </Box>
            ))}
          </SimpleGrid>
        </Box>
      ))}
      <PaginationFooter
        page={page}
        size={size}
        total={data!?.total}
        handleNextPage={handleNextPage}
        handlePreviousPage={handlePreviousPage}
      />
    </>
  );
};

export default ConnectionGrid;
