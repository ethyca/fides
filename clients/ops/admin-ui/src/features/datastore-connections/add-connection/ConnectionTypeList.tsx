import { Box, Center, SimpleGrid, Text } from "@fidesui/react";
import { ConnectionOption } from "connection-type/types";
import ConnectionTypeLogo from "datastore-connections/ConnectionTypeLogo";
import Link from "next/link";
import React from "react";

type ConnectionTypeListProps = {
  items: ConnectionOption[];
};

const ConnectionTypeList: React.FC<ConnectionTypeListProps> = ({ items }) => (
  <SimpleGrid columns={4} spacingX="16px" spacingY="16px">
    {items.map((i) => (
      <Link
        href={{
          pathname: window.location.pathname,
          query: { step: 2, connectorType: JSON.stringify(i) },
        }}
        key={i.identifier}
        passHref
      >
        <Box
          boxShadow="base"
          borderRadius="5px"
          maxWidth="232px"
          overflow="hidden"
          _hover={{
            boxShadow: "lg",
            cursor: "pointer",
          }}
        >
          <Center
            color="gray.700"
            fontSize="14px"
            fontStyle="normal"
            fontWeight="600"
            lineHeight="20px"
            h="80px"
          >
            <ConnectionTypeLogo data={i.identifier} />
            <Text ml="12px">{i.human_readable}</Text>
          </Center>
        </Box>
      </Link>
    ))}
  </SimpleGrid>
);

export default ConnectionTypeList;
