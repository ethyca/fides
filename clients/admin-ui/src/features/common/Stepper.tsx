import { Box, Stack, Text } from "@fidesui/react";
import React from "react";
import { StepperCircleIcon, VerticalLineIcon } from "./Icon";

const Stepper = (activeStep) => {
  const steps = [
    {
      number: 1,
      name: "Organization setup",
    },
    {
      number: 2,
      name: "Add a system",
    },
    {
      number: 3,
      name: "Authenticate scanner",
    },
    {
      number: 4,
      name: "Scan results",
    },
    {
      number: 5,
      name: "Describe systems",
    },
  ];

  return (
    <Stack direction={["column", "row"]}>
      <Stack alignItems={"center"} direction={"column"} spacing={0}>
        {/* if(activeStep === step.number) {
          color is green
        } */}
        <StepperCircleIcon boxSize={8} stroke={"secondary.500"} />
        <VerticalLineIcon boxSize={20} />
        <StepperCircleIcon boxSize={8} />
        <VerticalLineIcon boxSize={20} />
        <StepperCircleIcon boxSize={8} />
        <VerticalLineIcon boxSize={20} />
        <StepperCircleIcon boxSize={8} />
        <VerticalLineIcon boxSize={20} />
        <StepperCircleIcon boxSize={8} />
      </Stack>
      <Stack direction={"column"} spacing="24px">
        {steps.map((step) => (
          <Box>
            <Text>{step.number}</Text>
            <Text>{step.name}</Text>
          </Box>
        ))}
      </Stack>
    </Stack>
  );
};

export default Stepper;
