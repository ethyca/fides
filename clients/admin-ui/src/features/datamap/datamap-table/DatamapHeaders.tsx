import { Box, Text, Th, Thead, Tr } from "@fidesui/react";
import { HeaderGroup } from "react-table";

import { GRAY_BACKGROUND } from "~/features/datamap/constants";
import type { DatamapRow } from "~/features/datamap/datamap.slice";

const HeaderSpacer = () => (
  <Th
    padding={0}
    margin={0}
    width={4}
    borderBottomColor="gray.200"
    boxSizing="border-box"
  />
);

interface DatamapHeadersProps {
  headerGroups: HeaderGroup<DatamapRow>[];
}

const DatamapHeaders: React.FC<DatamapHeadersProps> = ({ headerGroups }) => (
  <Thead
    position="sticky"
    top="0px"
    height="36px"
    zIndex={10}
    backgroundColor={GRAY_BACKGROUND}
  >
    {headerGroups.map((headerGroup) => {
      const { key, ...headerProps } = headerGroup.getHeaderGroupProps();
      return (
        <Tr key={key} {...headerProps} height="inherit">
          <HeaderSpacer />
          {headerGroup.headers.map((column, index) => {
            const { key: columnKey, ...columnHeaderProps } =
              column.getHeaderProps();
            return (
              <Th
                key={columnKey}
                {...columnHeaderProps}
                title={`${column.Header}`}
                textTransform="none"
                px={2}
                display="flex"
                alignItems="center"
                borderLeftWidth={index === 0 ? "1px" : ""}
                borderRightWidth="1px"
                borderColor="gray.200"
              >
                <Text
                  whiteSpace="nowrap"
                  textOverflow="ellipsis"
                  overflow="hidden"
                  mr={1}
                >
                  {column.render("Header")}
                </Text>
                {column.canResize && (
                  <Box
                    {...column.getResizerProps()}
                    position="absolute"
                    top={0}
                    right={0}
                    width={2}
                    height="100%"
                    css={{
                      touchAction: ":none",
                    }}
                  />
                )}
              </Th>
            );
          })}
          <HeaderSpacer />
        </Tr>
      );
    })}
  </Thead>
);

export default DatamapHeaders;
