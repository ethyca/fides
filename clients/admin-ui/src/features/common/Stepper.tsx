import { Box, Stack, Text } from "@fidesui/react";
import React from "react";

import { StepperCircleIcon, VerticalLineIcon } from "./Icon";

interface Props {
  activeStep: number | null;
  steps: { number: number; name: string }[];
}

const Stepper = ({ activeStep, steps }: Props) => (
  <Stack direction={["column", "row"]} w="100%">
    <Stack alignItems="center" direction="column" spacing={0}>
      {steps.map((step) => (
        <React.Fragment key={step.number}>
          <StepperCircleIcon
            boxSize={8}
            stroke={activeStep === step.number ? "secondary.500" : "inherit"}
          />
          {step.number !== steps.length ? (
            <VerticalLineIcon boxSize={20} />
          ) : null}
        </React.Fragment>
      ))}
    </Stack>
    <Stack direction="column" justify="space-between">
      {steps.map((step) => (
        <Box key={step.name}>
          <Text color="gray.800">Step {step.number}</Text>
          <Text color="gray.500">{step.name}</Text>
        </Box>
      ))}
    </Stack>
  </Stack>
);

export default Stepper;
