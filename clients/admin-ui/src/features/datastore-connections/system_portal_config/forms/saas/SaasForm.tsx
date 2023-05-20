import { Box, SlideFade } from "@fidesui/react";
import TestConnection from "datastore-connections/add-connection/TestConnection";
import { useState } from "react";

import { useGetConnectionTypeSecretSchemaQuery } from "~/features/connection-type";
import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  SystemType,
} from "~/types/api";

import { SaasConnectorParameters } from "./ConnectorParameters";

type Props = {
  connectionConfig?: ConnectionConfigurationResponse;
  connectionOption: ConnectionSystemTypeMap;
  systemFidesKey: string;
};

export const SaasForm = ({
  connectionOption,
  systemFidesKey,
  connectionConfig,
}: Props) => {
  const skip = connectionOption.type === SystemType.MANUAL;

  const { data: secretsSchema } = useGetConnectionTypeSecretSchemaQuery(
    connectionOption!.identifier,
    {
      skip,
    }
  );
  const [response, setResponse] = useState<any>();

  const handleTestConnectionClick = (value: any) => {
    setResponse(value);
  };
  if (!secretsSchema) {
    return null;
  }

  return (
    <>
      <SaasConnectorParameters
        secretsSchema={secretsSchema}
        connectionOption={connectionOption}
        connectionConfig={connectionConfig}
        onTestConnectionClick={handleTestConnectionClick}
        systemFidesKey={systemFidesKey}
      />
      {response && (
        <SlideFade in>
          <Box mt="16px" maxW="528px" w="fit-content">
            <TestConnection response={response} />
          </Box>
        </SlideFade>
      )}
    </>
  );
};
