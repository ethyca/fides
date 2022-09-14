import { Box, Button, Grid, Stack, Text } from "@fidesui/react";
import { useState } from "react";

const STEPS = ["Describe", "Declare", "Review"];

interface ConfigureStepsProps {
  steps: string[];
  currentStepIndex: number;
  onChange: (index: number) => void;
}
const ConfigureSteps = ({
  steps,
  currentStepIndex,
  onChange,
}: ConfigureStepsProps) => (
  <Stack pl={5}>
    {steps.map((step, idx) => {
      const isActive = idx === currentStepIndex;
      return (
        <Button
          key={step}
          variant="ghost"
          colorScheme={isActive ? "complimentary" : "ghost"}
          width="fit-content"
          disabled={idx > currentStepIndex}
          onClick={() => onChange(idx)}
        >
          {step}
        </Button>
      );
    })}
  </Stack>
);

const ManualSystemFlow = () => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  return (
    <Grid templateColumns="2fr 8fr">
      <Stack spacing={3} fontWeight="semibold" data-testid="settings">
        <Text>Configuration Settings</Text>
        <ConfigureSteps
          steps={STEPS}
          currentStepIndex={currentStepIndex}
          onChange={setCurrentStepIndex}
        />
      </Stack>
      <Box>{STEPS[currentStepIndex]}</Box>
    </Grid>
  );
};

export default ManualSystemFlow;
