import { Button, Grid, GridItem, Stack, Text, VStack } from "@fidesui/react";
import { useFeatures } from "common/features";
import { useRouter } from "next/router";
import { useCallback, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import DataTabs, { TabData } from "~/features/common/DataTabs";
import { System } from "~/types/api";

import PrivacyDeclarationStep from "./PrivacyDeclarationStep";
import ReviewSystemStep from "./ReviewSystemStep";
import { selectActiveSystem, setActiveSystem } from "./system.slice";
import SystemInformationForm from "./SystemInformationForm";
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
  const {
    flags: { navV2 },
  } = useFeatures();

  const goBack = useCallback(() => {
    router.back();
    dispatch(setActiveSystem(undefined));
  }, [dispatch, router]);

  const handleSuccess = useCallback(
    (system: System) => {
      setCurrentStepIndex(currentStepIndex + 1);
      dispatch(setActiveSystem(system));
    },
    [currentStepIndex, dispatch]
  );

  const decrementStep = () => {
    setCurrentStepIndex(currentStepIndex - 1);
  };

  const TABS: TabData[] = [
    {
      label: STEPS[0],
      content: (
        <SystemInformationForm
          onSuccess={handleSuccess}
          onCancel={goBack}
          system={activeSystem}
          withHeader
        />
      ),
    },
    {
      label: STEPS[1],
      content: activeSystem ? (
        <PrivacyDeclarationStep
          system={activeSystem as System}
          onCancel={goBack}
          onSuccess={handleSuccess}
        />
      ) : null,
      isDisabled: !activeSystem,
    },
    {
      label: STEPS[2],
      content: activeSystem ? (
        <ReviewSystemStep
          system={activeSystem as System}
          onCancel={goBack}
          onSuccess={goBack}
        />
      ) : null,
      isDisabled: !activeSystem,
    },
  ];

  return (
    <>
      {navV2 && (
        <VStack alignItems="stretch" flex="1" gap="18px" maxWidth="70vw">
          <DataTabs
            data={TABS}
            data-testid="settings"
            flexGrow={1}
            index={currentStepIndex}
            isLazy
            onChange={setCurrentStepIndex}
          />
        </VStack>
      )}
      {!navV2 && (
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
              <SystemInformationForm
                onSuccess={handleSuccess}
                onCancel={goBack}
                system={activeSystem}
              />
            ) : null}
            {currentStepIndex === 1 && activeSystem ? (
              <PrivacyDeclarationStep
                system={activeSystem}
                onCancel={decrementStep}
                onSuccess={handleSuccess}
              />
            ) : null}
            {currentStepIndex === 2 && activeSystem ? (
              <ReviewSystemStep
                system={activeSystem}
                onCancel={decrementStep}
                onSuccess={() => setCurrentStepIndex(currentStepIndex + 1)}
              />
            ) : null}
            {currentStepIndex === 3 && activeSystem ? (
              <SystemRegisterSuccess
                system={activeSystem}
                onAddNextSystem={goBack}
              />
            ) : null}
          </GridItem>
        </Grid>
      )}
    </>
  );
};

export default ManualSystemFlow;
