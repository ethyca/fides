import { chunk } from "@chakra-ui/utils";
import { Box, SimpleGrid } from "@fidesui/react";
import React from "react";
import { useDispatch } from "react-redux";

import { useAppSelector } from "../../app/hooks";
import PaginationFooter from "../common/PaginationFooter";
import classes from "./ConnectionGrid.module.css";
import ConnectionGridItem from "./ConnectionGridItem";
import {
  selectDatastoreConnectionFilters,
  setPage,
} from "./datastore-connection.slice";
import { DatastoreConnection } from "./types";

const useConnectionGrid = () => {
  const dispatch = useDispatch();
  const filters = useAppSelector(selectDatastoreConnectionFilters);

  const handlePreviousPage = () => {
    dispatch(setPage(filters.page - 1));
  };

  const handleNextPage = () => {
    dispatch(setPage(filters.page + 1));
  };

  return {
    ...filters,
    handleNextPage,
    handlePreviousPage,
  };
};

type ConnectionGridProps = {
  items: DatastoreConnection[];
  total: number;
};

const ConnectionGrid: React.FC<ConnectionGridProps> = ({
  items = [],
  total = 0,
}) => {
  const { page, size, handleNextPage, handlePreviousPage } =
    useConnectionGrid();
  const columns = 3;
  const chunks = chunk(items, columns);

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
        total={total}
        handleNextPage={handleNextPage}
        handlePreviousPage={handlePreviousPage}
      />
    </>
  );
};

export default ConnectionGrid;
