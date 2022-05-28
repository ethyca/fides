import { Box, Stack, Text } from "@fidesui/react";
import React from "react";
import { StepperCircleIcon, VerticalLineIcon } from "./Icon";

const Stepper = () => {
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
    <Stack direction={["column", "row"]} spacing="24px">
      <Stack direction={"column"} spacing="24px">
        <Box>line</Box>
        <StepperCircleIcon height={8} width={8} />
        <VerticalLineIcon height={20} width={20} />
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
