import { Button, Grid, GridItem, Stack, Text, VStack } from "@fidesui/react";
import { useRouter } from "next/router";
import { useCallback, useMemo, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import DataTabs, { TabData } from "~/features/common/DataTabs";
import { System } from "~/types/api";

import { useFeatures } from "../common/features.slice";
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
  const { navV2 } = useFeatures();

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

  const getTabs = useMemo(
    () => () => {
      const result: TabData[] = [];
      STEPS.forEach((step, index) => {
        let data: TabData | undefined;
        switch (index) {
          case 0:
            data = {
              label: step,
              content: (
                <DescribeSystemStep
                  onSuccess={handleSuccess}
                  system={activeSystem}
                />
              ),
            };
            break;
          case 1:
            data = {
              label: step,
              content: activeSystem ? (
                <PrivacyDeclarationStep
                  system={activeSystem as System}
                  onSuccess={handleSuccess}
                />
              ) : null,
              isDisabled: !activeSystem,
            };
            break;
          case 2:
            data = {
              label: step,
              content: activeSystem ? (
                <ReviewSystemStep
                  system={activeSystem as System}
                  onSuccess={() => setCurrentStepIndex(currentStepIndex + 1)}
                />
              ) : null,
              isDisabled: !activeSystem,
            };
            break;
          case 3:
            data = {
              label: step,
              content: activeSystem ? (
                <SystemRegisterSuccess
                  system={activeSystem as System}
                  onAddNextSystem={goBack}
                />
              ) : null,
              isDisabled: !activeSystem,
            };
            break;
          default:
            break;
        }
        if (data) {
          result.push(data);
        }
      });
      return result;
    },
    [activeSystem, currentStepIndex, goBack, handleSuccess]
  );

  return (
    <>
      {navV2 && (
        <VStack alignItems="stretch" flex="1" gap="18px" maxWidth="70vw">
          <DataTabs
            data={getTabs()}
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
              <DescribeSystemStep
                onSuccess={handleSuccess}
                system={activeSystem}
              />
            ) : null}
            {currentStepIndex === 1 && activeSystem ? (
              <PrivacyDeclarationStep
                system={activeSystem}
                onSuccess={handleSuccess}
              />
            ) : null}
            {currentStepIndex === 2 && activeSystem ? (
              <ReviewSystemStep
                system={activeSystem}
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
