import { Stack } from "@fidesui/react";
import React from "react";

// import { StepperCircleIcon, VerticalLineIcon } from "./Icon";

// interface Props {
//   activeStep: number | null;
//   steps: { number: number; name: string }[];
// }

const HorizontalStepper = () => (
  // { activeStep, steps }: Props
  <Stack direction={["row"]} w="100%">
    <Stack alignItems="center" direction="row" spacing={0}>
      Horizontal Stepper
    </Stack>
  </Stack>
);

export default HorizontalStepper;
