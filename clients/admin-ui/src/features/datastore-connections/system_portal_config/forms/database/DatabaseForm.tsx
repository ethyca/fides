import { DatabaseConnectorParameters } from "./ConnectorParameters";
import { useGetConnectionTypeSecretSchemaQuery } from "~/features/connection-type";
import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  SystemType,
} from "~/types/api";
import { useState } from "react";
import TestConnection from "datastore-connections/add-connection/TestConnection";
import { SlideFade, Box } from "@fidesui/react";

type Props = {
  connectionConfig?: ConnectionConfigurationResponse;
  connectionOption: ConnectionSystemTypeMap;
  systemFidesKey: string;
};

export const DatabaseForm = ({
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
      <DatabaseConnectorParameters
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
