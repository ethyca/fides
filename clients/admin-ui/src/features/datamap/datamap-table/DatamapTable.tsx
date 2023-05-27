import { Box, Table, Tbody, Td, Text, Tr } from "@fidesui/react";
import React, { useContext } from "react";

import {
  GRAY_BACKGROUND,
  SYSTEM_FIDES_KEY_COLUMN_ID,
} from "~/features/datamap/constants";
import DatamapTableContext from "~/features/datamap/datamap-table/DatamapTableContext";
import { SetSelectedSystemId } from "~/features/datamap/types";

import DatamapHeaders from "./DatamapHeaders";

type DatamapTableProps = {} & SetSelectedSystemId;
const DatamapTable = ({ setSelectedSystemId }: DatamapTableProps) => {
  const { tableInstance } = useContext(DatamapTableContext);
  if (!tableInstance) {
    return null;
  }

  const { getTableProps, getTableBodyProps, headerGroups, prepareRow, rows } =
    tableInstance;

  return (
    <Box boxSize="100%" overflow="auto">
      <Table {...getTableProps()} size="sm" data-testid="datamap-table">
        <DatamapHeaders headerGroups={headerGroups} />
        <Tbody backgroundColor={GRAY_BACKGROUND} {...getTableBodyProps()}>
          {rows.map((row) => {
            prepareRow(row);

            const groupHeader = (
              <Tr
                {...row.getRowProps()}
                borderTopLeftRadius="6px"
                borderTopRightRadius="6px"
                height="70px"
                backgroundColor="gray.50"
                borderWidth="1px"
                borderBottom="none"
                mt={4}
                ml={4}
                mr={4}
                key={row.groupByVal}
              >
                <Td
                  colSpan={row.cells.length}
                  {...row.cells[0].getCellProps()}
                  width="auto"
                  paddingX={2}
                >
                  <Text
                    fontSize="xs"
                    lineHeight={4}
                    fontWeight="500"
                    color="gray.600"
                    textTransform="uppercase"
                    pb={2}
                    pt={1}
                  >
                    System Name
                  </Text>

                  <Text
                    fontSize="sm"
                    lineHeight={5}
                    fontWeight="bold"
                    color="gray.600"
                  >
                    {row.groupByVal}
                  </Text>
                </Td>
              </Tr>
            );

            const groupedRows = row.subRows.map((subRow, index) => {
              prepareRow(subRow);
              const { key, ...rowProps } = subRow.getRowProps();
              return (
                <Tr
                  key={key}
                  minHeight={9}
                  borderWidth="1px"
                  borderColor="gray.200"
                  borderTop="none"
                  borderBottomLeftRadius={
                    index === row.subRows.length - 1 ? "6px" : ""
                  }
                  borderBottomRightRadius={
                    index === row.subRows.length - 1 ? "6px" : ""
                  }
                  {...rowProps}
                  _hover={{
                    bg: "gray.50",
                  }}
                  cursor="pointer"
                  backgroundColor="white"
                  onClick={() => {
                    if (subRow.values[SYSTEM_FIDES_KEY_COLUMN_ID]) {
                      setSelectedSystemId(
                        subRow.values[SYSTEM_FIDES_KEY_COLUMN_ID]
                      );
                    }
                  }}
                  ml={4}
                  mr={4}
                  _last={{
                    mb: 4,
                  }}
                >
                  {subRow.cells.map((cell, cellIndex) => {
                    const { key: cellKey, ...cellProps } = cell.getCellProps();
                    return (
                      <Td
                        key={cellKey}
                        {...cellProps}
                        borderRightWidth={
                          cellIndex === subRow.cells.length - 1 ? "" : "1px"
                        }
                        borderBottom="none"
                        borderColor="gray.200"
                        padding={0}
                      >
                        {cell.render("Cell")}
                      </Td>
                    );
                  })}
                </Tr>
              );
            });

            return [groupHeader, groupedRows];
          })}
        </Tbody>
      </Table>
    </Box>
  );
};

export default DatamapTable;
