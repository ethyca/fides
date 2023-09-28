import { Stack, Tbody, Td, Text, Tr } from "@fidesui/react";
import { Row, UseTableInstanceProps } from "react-table";

import { GRAY_BACKGROUND } from "./constants";

type Props<T extends object> = {
  rowHeading?: string;
  renderRowSubheading: (row: Row<T>) => string;
  renderOverflowMenu?: (row: Row<T>) => React.ReactNode;
  onSubrowClick?: (row: Row<T>) => void;
} & Pick<UseTableInstanceProps<T>, "getTableBodyProps" | "rows" | "prepareRow">;

const GroupedTableBody = <T extends object>({
  rowHeading,
  renderRowSubheading,
  renderOverflowMenu,
  rows,
  prepareRow,
  getTableBodyProps,
  onSubrowClick,
}: Props<T>) => (
  <Tbody backgroundColor={GRAY_BACKGROUND} {...getTableBodyProps()}>
    {rows.map((row) => {
      prepareRow(row);

      const groupHeader = (
        <Tr
          {...row.getRowProps()}
          borderTopLeftRadius="6px"
          borderTopRightRadius="6px"
          backgroundColor="gray.50"
          borderWidth="1px"
          borderBottom="none"
          mt={4}
          ml={4}
          mr={4}
          key={row.groupByVal}
          data-testid={`grouped-row-${row.groupByVal}`}
        >
          <Td
            display="flex"
            justifyContent="space-between"
            colSpan={row.cells.length}
            {...row.cells[0].getCellProps()}
            width="auto"
            paddingX={2}
          >
            <Stack>
              {rowHeading ? (
                <Text
                  fontSize="xs"
                  lineHeight={4}
                  fontWeight="500"
                  color="gray.600"
                  textTransform="uppercase"
                  pb={2}
                  pt={1}
                >
                  {rowHeading}
                </Text>
              ) : null}

              <Text
                fontSize="sm"
                lineHeight={5}
                fontWeight="bold"
                color="gray.600"
                mb={1}
              >
                {renderRowSubheading(row)}
              </Text>
            </Stack>
            {renderOverflowMenu ? renderOverflowMenu(row) : null}
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
            cursor={onSubrowClick ? "pointer" : undefined}
            backgroundColor="white"
            onClick={onSubrowClick ? () => onSubrowClick(subRow) : undefined}
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
                  data-testid={`subrow-${cellKey}`}
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
);

export default GroupedTableBody;
