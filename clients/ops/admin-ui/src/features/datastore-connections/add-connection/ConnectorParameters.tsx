import { Box, Center, Flex, Spinner, VStack } from "@fidesui/react";
import { capitalize } from "common/utils";
import { useGetConnectionTypeSecretSchemaQuery } from "connection-type/connection-type.slice";
import { ConnectionOption } from "connection-type/types";
import React, { useState } from "react";

import { STEPS } from "./constants";
import { ConnectorParameters as SassConnectorParametersForm } from "./sass/ConnectorParameters";
import TestConnection from "./TestConnection";
import { AddConnectionStep } from "./types";

type ConnectorParametersProps = {
  currentStep: AddConnectionStep;
  connectionOption: ConnectionOption;
};

export const ConnectorParameters: React.FC<ConnectorParametersProps> = ({
  currentStep = STEPS.filter((s) => s.stepId === 2)[0],
  connectionOption,
}) => {
  const { data, isFetching, isLoading, isSuccess } =
    useGetConnectionTypeSecretSchemaQuery(connectionOption.identifier);
  const [response, setResponse] = useState<any>();

  const handleTestConnectionClick = (value: any) => {
    setResponse(value);
  };

  return (
    <Flex gap="97px">
      <VStack w="579px" gap="24px" align="stretch">
        <Box color="gray.700" fontSize="14px" h="80px" w="475px">
          {currentStep.description?.replace(
            "{identifier}",
            capitalize(connectionOption.identifier)
          )}
        </Box>
        {(isFetching || isLoading) && (
          <Center>
            <Spinner />
          </Center>
        )}
        {isSuccess && data ? (
          <SassConnectorParametersForm
            connectionOption={connectionOption}
            data={data}
            onTestConnectionClick={handleTestConnectionClick}
          />
        ) : null}
      </VStack>
      {response && (
        <Box w="480px" mt="16px">
          <TestConnection
            connectionOption={connectionOption}
            response={response}
          />
        </Box>
      )}
    </Flex>
  );
};

export default ConnectorParameters;
