import { Stack, Text } from "@fidesui/react";
import React from "react";
import { HorizontalLineIcon } from "../common/Icon/index";

interface Props {
  activeStep: number | null;
  steps: { number: number; name: string }[];
}

const HorizontalStepper = ({ activeStep, steps }: Props) => (
  <Stack alignItems="flex-start" direction={["row"]} w="100%">
    {steps.map((step) => (
      <React.Fragment key={step.number}>
        {activeStep && activeStep === step.number ? (
          <>
            <Stack direction={["row"]}>
              {/* should have colors */}
              <HorizontalLineIcon boxSize={20} />
              <Stack>
                <Text>{step.name}</Text>
              </Stack>
            </Stack>
          </>
        ) : (
          <>
            <Stack direction={["row"]}>
              <HorizontalLineIcon boxSize={20} />
              <Stack>
                <Text>{step.name}</Text>
              </Stack>
            </Stack>
          </>
        )}
      </React.Fragment>
    ))}
  </Stack>
);

export default HorizontalStepper;
