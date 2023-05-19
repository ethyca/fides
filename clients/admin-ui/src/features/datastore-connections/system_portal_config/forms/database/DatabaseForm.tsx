import { DatabaseConnectorParameters } from "./ConnectorParameters";
import {
  useGetConnectionTypeSecretSchemaQuery,
} from "~/features/connection-type";
import { ConnectionSystemTypeMap, SystemType } from "~/types/api";
import { useState } from "react";
import TestConnection from "datastore-connections/add-connection/TestConnection";
import { SlideFade, Box } from "@fidesui/react";

type Props = {
  connectionOption: ConnectionSystemTypeMap;
  systemFidesKey: string;
};

export const DatabaseForm = ({ connectionOption, systemFidesKey }: Props) => {
  const skip = connectionOption.type === SystemType.MANUAL;

  const { data, isFetching, isLoading, isSuccess } =
    useGetConnectionTypeSecretSchemaQuery(connectionOption!.identifier, {
      skip,
    });

  const [response, setResponse] = useState<any>();

  const handleTestConnectionClick = (value: any) => {
    setResponse(value);
  };
  if (!data) {
    return null;
  }




  return (
    <>
      <DatabaseConnectorParameters
        data={data}
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
