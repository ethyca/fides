import { Box, Stack, Text } from "@fidesui/react";
import React from "react";
import { StepperCircleIcon, VerticalLineIcon } from "./Icon";

interface Props {
  activeStep: number | null;
}

const Stepper = ({ activeStep }: Props) => {
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
        {steps?.map((step: any) => (
          <>
            <StepperCircleIcon
              boxSize={8}
              stroke={activeStep === step.number ? "secondary.500" : "inherit"}
            />
            {step.number !== 5 ? <VerticalLineIcon boxSize={20} /> : null}
          </>
        ))}
      </Stack>
      <Stack direction={"column"} justify={"space-between"}>
        {steps?.map((step: any) => (
          <Box>
            <Text color="gray.800">Step {step.number}</Text>
            <Text color="gray.500">{step.name}</Text>
          </Box>
        ))}
      </Stack>
    </Stack>
  );
};

export default Stepper;
