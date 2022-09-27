import { Box, Center, Flex, SlideFade, Spinner, VStack } from "@fidesui/react";
import { useAppSelector } from "app/hooks";
import {
  selectConnectionTypeState,
  useGetConnectionTypeSecretSchemaQuery,
} from "connection-type/connection-type.slice";
import { SystemType } from "datastore-connections/constants";
import React, { useCallback, useEffect, useRef, useState } from "react";

import { ConnectorParameters as DatabaseConnectorParameters } from "./database/ConnectorParameters";
import { replaceURL } from "./helpers";
import { ConnectorParameters as ManualConnectorParameters } from "./manual/ConnectorParameters";
import { ConnectorParameters as SassConnectorParameters } from "./sass/ConnectorParameters";
import TestConnection from "./TestConnection";

type ConnectorParametersProp = {
  onConnectionCreated: () => void;
};

export const ConnectorParameters: React.FC<ConnectorParametersProp> = ({
  onConnectionCreated,
}) => {
  const mounted = useRef(false);
  const [skip, setSkip] = useState(true);
  const { connection, connectionOption, step } = useAppSelector(
    selectConnectionTypeState
  );

  const { data, isFetching, isLoading, isSuccess } =
    useGetConnectionTypeSecretSchemaQuery(connectionOption!.identifier, {
      skip,
    });
  const [response, setResponse] = useState<any>();

  const handleTestConnectionClick = (value: any) => {
    setResponse(value);
  };

  // eslint-disable-next-line consistent-return
  const getComponent = useCallback(() => {
    // eslint-disable-next-line default-case
    switch (connectionOption?.type) {
      case SystemType.DATABASE:
        if (isSuccess && data) {
          return (
            <DatabaseConnectorParameters
              data={data}
              onConnectionCreated={onConnectionCreated}
              onTestConnectionClick={handleTestConnectionClick}
            />
          );
        }
        break;
      case SystemType.MANUAL:
        return (
          <ManualConnectorParameters
            onConnectionCreated={onConnectionCreated}
          />
        );
        break;
      case SystemType.SAAS:
        if (isSuccess && data) {
          return (
            <SassConnectorParameters
              data={data}
              onConnectionCreated={onConnectionCreated}
              onTestConnectionClick={handleTestConnectionClick}
            />
          );
        }
        break;
    }
  }, [connectionOption?.type, data, isSuccess, onConnectionCreated]);

  useEffect(() => {
    mounted.current = true;
    if (connection?.key) {
      replaceURL(connection.key, step.href);
    }
    if (connectionOption?.type !== SystemType.MANUAL) {
      setSkip(false);
    }
    return () => {
      mounted.current = false;
    };
  }, [connection?.key, connectionOption?.type, step.href]);

  return (
    <Flex gap="97px">
      <VStack w="579px" gap="24px" align="stretch">
        {(isFetching || isLoading) && (
          <Center>
            <Spinner />
          </Center>
        )}
        {getComponent()}
      </VStack>
      {response && (
        <SlideFade in>
          {" "}
          <Box mt="16px" w="fit-content">
            <TestConnection response={response} />
          </Box>
        </SlideFade>
      )}
    </Flex>
  );
};

export default ConnectorParameters;
