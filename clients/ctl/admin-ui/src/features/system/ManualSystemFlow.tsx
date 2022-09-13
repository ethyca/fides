import { Button, Grid, GridItem, Stack, Text } from "@fidesui/react";
import { useRouter } from "next/router";
import { useState } from "react";

import { System } from "~/types/api";

import DescribeSystemsForm from "../config-wizard/DescribeSystemsForm";
import PrivacyDeclarationForm from "../config-wizard/PrivacyDeclarationForm";
import ReviewSystemForm from "../config-wizard/ReviewSystemForm";

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
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [newSystem, setNewSystem] = useState<System | null>(null);

  const handleCancel = () => {
    router.push("/system/new");
  };

  const handleDescribeSuccess = (system: System) => {
    setCurrentStepIndex(currentStepIndex + 1);
    setNewSystem(system);
  };

  const handleDeclareSuccess = () => {
    setCurrentStepIndex(currentStepIndex + 1);
  };

  const handleReviewSuccess = () => {
    router.push("/system");
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
            systemKey={newSystem.fides_key}
            onSuccess={handleDeclareSuccess}
            onCancel={handleCancel}
          />
        ) : null}
        {currentStepIndex === 2 && newSystem ? (
          <ReviewSystemForm
            systemKey={newSystem.fides_key}
            onCancel={handleCancel}
            onSuccess={handleReviewSuccess}
          />
        ) : null}
      </GridItem>
    </Grid>
  );
};

export default ManualSystemFlow;
