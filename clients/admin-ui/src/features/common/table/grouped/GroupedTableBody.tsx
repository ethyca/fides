import { Tbody, Td, Text, Tr } from "@fidesui/react";
import { Row, UseGroupByRowProps, UseTableInstanceProps } from "react-table";

import { GRAY_BACKGROUND } from "./constants";

type Props<T extends object> = {
  heading?: string;
  titleKey: keyof UseGroupByRowProps<T>;
  onRowClick: (row: Row<T>) => void;
} & Pick<UseTableInstanceProps<T>, "getTableBodyProps" | "rows" | "prepareRow">;

const GroupedTableBody = <T extends object>({
  heading,
  titleKey,
  rows,
  prepareRow,
  getTableBodyProps,
  onRowClick,
}: Props<T>) => (
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
            {heading ? (
              <Text
                fontSize="xs"
                lineHeight={4}
                fontWeight="500"
                color="gray.600"
                textTransform="uppercase"
                pb={2}
                pt={1}
              >
                {heading}
              </Text>
            ) : null}

            <Text
              fontSize="sm"
              lineHeight={5}
              fontWeight="bold"
              color="gray.600"
            >
              {row[titleKey]}
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
            onClick={() => onRowClick(subRow)}
            // onClick={() => {
            //   if (subRow.values[SYSTEM_FIDES_KEY_COLUMN_ID]) {
            //     setSelectedSystemId(subRow.values[SYSTEM_FIDES_KEY_COLUMN_ID]);
            //   }
            // }}
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
);

export default GroupedTableBody;
