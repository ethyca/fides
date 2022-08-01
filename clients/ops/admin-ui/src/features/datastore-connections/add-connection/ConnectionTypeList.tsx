import { Box, Center, Image, SimpleGrid } from "@fidesui/react";
import {
  CONNECTION_TYPE_LOGO_MAP,
  CONNECTOR_LOGOS_PATH,
  FALLBACK_CONNECTOR_LOGOS_PATH,
} from "datastore-connections/constants";
import React from "react";

import { ConnectionOption } from "../../connection-type/types";

type ConnectionTypeListProps = {
  items: ConnectionOption[];
};

const ConnectionTypeList: React.FC<ConnectionTypeListProps> = ({ items }) => {
  const getImageSrc = (value: string): string => {
    const item = [...CONNECTION_TYPE_LOGO_MAP].find(
      ([k]) => k.toLowerCase() === value.toLowerCase()
    );
    const path = item
      ? CONNECTOR_LOGOS_PATH + item[1]
      : FALLBACK_CONNECTOR_LOGOS_PATH;
    return path;
  };

  return (
    <SimpleGrid columns={4} spacing="16px">
      {items.map((i) => (
        <Box
          boxShadow="base"
          borderRadius="5px"
          key={JSON.stringify(i)}
          maxWidth="232px"
          overflow="hidden"
        >
          <Center
            color="gray.700"
            fontSize="14px"
            fontStyle="normal"
            fontWeight="600"
            lineHeight="20px"
            h="80px"
          >
            <Image
              boxSize="32px"
              marginRight="12px"
              objectFit="cover"
              src={`/${getImageSrc(i.identifier)}`}
              fallbackSrc={`/${FALLBACK_CONNECTOR_LOGOS_PATH}`}
              alt={i.identifier}
            />
            {i.identifier}
          </Center>
        </Box>
      ))}
    </SimpleGrid>
  );
};

export default ConnectionTypeList;
