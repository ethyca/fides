import { Box, Center, Flex, SlideFade, Spinner, VStack } from "@fidesui/react";
import {
  selectConnectionTypeState,
  useGetConnectionTypeSecretSchemaQuery,
} from "connection-type/connection-type.slice";
import React, { useCallback, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { SystemType } from "~/types/api";

import { ConnectorParameters as DatabaseConnectorParameters } from "./database/ConnectorParameters";
import { ConnectorParameters as EmailConnectorParameters } from "./email/ConnectorParameters";
import { ConnectorParameters as ManualConnectorParameters } from "./manual/ConnectorParameters";
import { ConnectorParameters as SassConnectorParameters } from "./sass/ConnectorParameters";
import TestConnection from "./TestConnection";

type ConnectorParametersProp = {
  onConnectionCreated?: () => void;
};

export const ConnectorParameters: React.FC<ConnectorParametersProp> = ({
  onConnectionCreated,
}) => {
  const { connectionOption } = useAppSelector(selectConnectionTypeState);
  const skip = connectionOption && connectionOption.type === SystemType.MANUAL;
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
      case SystemType.EMAIL:
        if (isSuccess && data) {
          return (
            <EmailConnectorParameters
              data={data}
              onConnectionCreated={onConnectionCreated}
              onTestConnectionClick={handleTestConnectionClick}
            />
          );
        }
    }
  }, [connectionOption?.type, data, isSuccess, onConnectionCreated]);

  return (
    <Flex gap="97px">
      <VStack w="579px" gap="16px" align="stretch">
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
          <Box mt="16px" maxW="528px" w="fit-content">
            <TestConnection response={response} />
          </Box>
        </SlideFade>
      )}
    </Flex>
  );
};

export default ConnectorParameters;
