import { Box, Stack, Text } from "@fidesui/react";
import React from "react";

import {
  StepperCircleCheckmarkIcon,
  StepperCircleIcon,
  VerticalLineIcon,
} from "./Icon";

interface Props {
  activeStep: number | null;
  setActiveStep: Function;
  steps: { number: number; name: string }[];
}

const Stepper = ({ activeStep, setActiveStep, steps }: Props) => (
  <Stack direction={["column", "row"]}>
    <Stack alignItems="center" direction="column" spacing={0}>
      {steps.map((step) => (
        <React.Fragment key={step.number}>
          {activeStep &&
          activeStep !== 1 &&
          activeStep !== step.number &&
          activeStep > step.number - 1 ? (
            <StepperCircleCheckmarkIcon
              boxSize={8}
              cursor={step.number < activeStep ? "pointer" : "default"}
              onClick={() => {
                if (step.number < activeStep) {
                  setActiveStep(step.number);
                }
              }}
            />
          ) : (
            <StepperCircleIcon
              boxSize={8}
              cursor={
                activeStep && step.number < activeStep ? "pointer" : "default"
              }
              onClick={() => {
                if (activeStep && step.number < activeStep) {
                  setActiveStep(step.number);
                }
              }}
            />
          )}
          {step.number !== steps.length ? (
            <VerticalLineIcon boxSize={20} />
          ) : null}
        </React.Fragment>
      ))}
    </Stack>
    <Stack direction="column" justify="space-between" minW="100%">
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
