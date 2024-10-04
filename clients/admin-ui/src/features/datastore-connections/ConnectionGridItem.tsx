import { formatDate } from "common/utils";
import { AntButton, Box, Flex, Spacer, Text } from "fidesui";
import React, { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import { selectConnectionTypeState } from "~/features/connection-type";
import { ConnectionConfigurationResponse } from "~/types/api";

import ConnectionMenu from "./ConnectionMenu";
import ConnectionStatusBadge from "./ConnectionStatusBadge";
import ConnectionTypeLogo from "./ConnectionTypeLogo";
import { useLazyGetDatastoreConnectionStatusQuery } from "./datastore-connection.slice";
import { TestData } from "./TestData";

type ConnectionGridItemProps = {
  connectionData: ConnectionConfigurationResponse;
};

const ConnectionGridItem = ({ connectionData }: ConnectionGridItemProps) => {
  const [trigger, result] = useLazyGetDatastoreConnectionStatusQuery();
  const { connectionOptions } = useAppSelector(selectConnectionTypeState);

  const connectionType = useMemo(
    () =>
      connectionOptions.find(
        (ct) =>
          ct.identifier === connectionData.connection_type ||
          (connectionData.saas_config &&
            ct.identifier === connectionData.saas_config.type),
      ) || "ethyca",
    [connectionData, connectionOptions],
  );

  return (
    <Box
      width="100%"
      height={136}
      p="18px 16px 16px 16px"
      data-testid={`connection-grid-item-${connectionData.name}`}
    >
      <Flex justifyContent="center" alignItems="center">
        <ConnectionTypeLogo data={connectionType} />
        <Text
          color="gray.900"
          fontSize="md"
          fontWeight="medium"
          m="8px"
          textOverflow="ellipsis"
          overflow="hidden"
          whiteSpace="nowrap"
        >
          {connectionData.name}
        </Text>
        <Spacer />
        <ConnectionStatusBadge disabled={!!connectionData.disabled} />
        <ConnectionMenu
          connection_key={connectionData.key}
          disabled={!!connectionData.disabled}
          name={connectionData.name ?? connectionData.key}
          connection_type={connectionData.connection_type}
          access_type={connectionData.access}
        />
      </Flex>
      <Text color="gray.600" fontSize="sm" fontWeight="sm" lineHeight="20px">
        {/* If description is empty display empty placeholder */}
        {connectionData.description ? connectionData.description : <br />}
      </Text>
      <Text color="gray.600" fontSize="sm" fontWeight="sm" lineHeight="20px">
        Edited on {formatDate(connectionData.updated_at!)}
      </Text>

      <Flex mt="0px" justifyContent="center" alignItems="center">
        <TestData
          succeeded={connectionData.last_test_succeeded}
          timestamp={connectionData.last_test_timestamp || ""}
        />
        <Spacer />
        <AntButton
          size="small"
          onClick={() => {
            trigger(connectionData.key);
          }}
          loading={result.isLoading || result.isFetching}
        >
          Test
        </AntButton>
      </Flex>
    </Box>
  );
};

export default ConnectionGridItem;
