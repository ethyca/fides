import { Box, VStack } from "@fidesui/react";
import { capitalize } from "common/utils";
import { ConnectionOption } from "connection-type/types";
import React from "react";

import { STEPS } from "../constants";
import { AddConnectionStep } from "../types";

type DatasetConfigurationProps = {
  connectionOption: ConnectionOption;
  currentStep: AddConnectionStep;
};

const DatasetConfiguration: React.FC<DatasetConfigurationProps> = ({
  connectionOption,
  currentStep = STEPS.filter((s) => s.stepId === 3)[0],
}) => (
  <VStack align="stretch">
    <Box color="gray.700" fontSize="14px" h="80px" w="475px">
      {currentStep.description?.replace(
        "{identifier}",
        capitalize(connectionOption.identifier)
      )}
    </Box>
  </VStack>
);

export default DatasetConfiguration;
