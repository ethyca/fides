import { HorizontalLineIcon, Stack, Text } from "fidesui";
import React from "react";

interface Props {
  activeStep: number | null;
  steps: { number: number; name: string }[];
}

const HorizontalStepper = ({ activeStep, steps }: Props) => (
  <Stack alignItems="flex-start" direction={["row"]} w="100%">
    {steps.map((step) => (
      <React.Fragment key={step.number}>
        {activeStep && activeStep === step.number ? (
          <Stack alignItems="baseline" direction={["column"]}>
            <HorizontalLineIcon color="#824EF2" />
            <Text color="#805AD5">{step.name}</Text>
          </Stack>
        ) : (
          <Stack alignItems="baseline" direction={["column"]}>
            <HorizontalLineIcon />
            <Text>{step.name}</Text>
          </Stack>
        )}
      </React.Fragment>
    ))}
  </Stack>
);

export default HorizontalStepper;
