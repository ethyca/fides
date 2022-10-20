import { Button, Grid, GridItem, Stack, Text } from "@fidesui/react";
import { useRouter } from "next/router";
import { useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { System } from "~/types/api";

import DescribeSystemStep from "./DescribeSystemStep";
import PrivacyDeclarationStep from "./PrivacyDeclarationStep";
import ReviewSystemStep from "./ReviewSystemStep";
import { selectActiveSystem, setActiveSystem } from "./system.slice";
import SystemRegisterSuccess from "./SystemRegisterSuccess";

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
  const dispatch = useAppDispatch();

  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const activeSystem = useAppSelector(selectActiveSystem);

  const goBack = () => {
    router.back();
    dispatch(setActiveSystem(undefined));
  };

  const handleSuccess = (system: System) => {
    setCurrentStepIndex(currentStepIndex + 1);
    dispatch(setActiveSystem(system));
  };

  const goToIndex = () => {
    router.push("/system");
    dispatch(setActiveSystem(undefined));
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
          <DescribeSystemStep
            onSuccess={handleSuccess}
            onCancel={goBack}
            system={activeSystem}
          />
        ) : null}
        {currentStepIndex === 1 && activeSystem ? (
          <PrivacyDeclarationStep
            system={activeSystem}
            onSuccess={handleSuccess}
            onCancel={goBack}
          />
        ) : null}
        {currentStepIndex === 2 && activeSystem ? (
          <ReviewSystemStep
            system={activeSystem}
            onCancel={goBack}
            onSuccess={() => setCurrentStepIndex(currentStepIndex + 1)}
          />
        ) : null}
        {currentStepIndex === 3 && activeSystem ? (
          <SystemRegisterSuccess
            system={activeSystem}
            onAddNextSystem={goBack}
            onContinue={goToIndex}
          />
        ) : null}
      </GridItem>
    </Grid>
  );
};

export default ManualSystemFlow;
