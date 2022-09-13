import { Button, Grid, GridItem, Stack, Text } from "@fidesui/react";
import { useRouter } from "next/router";
import { useState } from "react";

import { System } from "~/types/api";

import DescribeSystemsForm from "../config-wizard/DescribeSystemsForm";
import PrivacyDeclarationForm from "../config-wizard/PrivacyDeclarationForm";

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
  const router = useRouter();
  const [currentStepIndex, setCurrentStepIndex] = useState(1);
  const [newSystem, setNewSystem] = useState<System | null>(null);

  const handleCancel = () => {
    router.push("/system/new");
  };

  const handleDescribeSuccess = (system: System) => {
    setCurrentStepIndex(currentStepIndex + 1);
    setNewSystem(system);
  };

  return (
    <Grid templateColumns="3fr 7fr" maxWidth="70vw">
      <GridItem>
        <Stack spacing={3} fontWeight="semibold" data-testid="settings">
          <Text>Configuration Settings</Text>
          <ConfigureSteps
            steps={STEPS}
            currentStepIndex={currentStepIndex}
            onChange={setCurrentStepIndex}
          />
        </Stack>
      </GridItem>
      <GridItem w="75%">
        {currentStepIndex === 0 ? (
          <DescribeSystemsForm
            onSuccess={handleDescribeSuccess}
            onCancel={handleCancel}
          />
        ) : null}
        {currentStepIndex === 1 && newSystem ? (
          <PrivacyDeclarationForm
            systemKey={newSystem?.fides_key}
            onCancel={handleCancel}
          />
        ) : null}
      </GridItem>
    </Grid>
  );
};

export default ManualSystemFlow;
