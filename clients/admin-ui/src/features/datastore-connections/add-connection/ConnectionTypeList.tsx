import ConnectionTypeLogo from "datastore-connections/ConnectionTypeLogo";
import { Box, Flex, SimpleGrid, Text } from "fidesui";
import NextLink from "next/link";
import React from "react";

import { ConnectionSystemTypeMap } from "~/types/api";

type ConnectionTypeListProps = {
  items: ConnectionSystemTypeMap[];
};

const ConnectionTypeList = ({ items }: ConnectionTypeListProps) => (
  <SimpleGrid columns={4} spacingX="16px" spacingY="16px">
    {items.map((i) => (
      <NextLink
        href={{
          pathname: window.location.pathname,
          query: { step: 2, connectorType: JSON.stringify(i) },
        }}
        key={i.identifier}
      >
        <Box
          boxShadow="base"
          borderRadius="5px"
          maxWidth="331px"
          overflow="hidden"
          _hover={{
            boxShadow: "lg",
            cursor: "pointer",
          }}
          data-testid={`${i.identifier}-item`}
        >
          <Flex
            alignItems="center"
            justifyContent="start"
            pl="24px"
            pr="24px"
            color="gray.700"
            fontSize="14px"
            fontStyle="normal"
            fontWeight="600"
            lineHeight="20px"
            h="80px"
          >
            <ConnectionTypeLogo data={i} />
            <Text ml="12px">{i.human_readable}</Text>
          </Flex>
        </Box>
      </NextLink>
    ))}
  </SimpleGrid>
);

export default ConnectionTypeList;
