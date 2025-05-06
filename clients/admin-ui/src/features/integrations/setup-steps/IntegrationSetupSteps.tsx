import {
  AntCard as Card,
  AntSteps as Steps,
  Icons,
  StepperCircleCheckmarkIcon,
} from "fidesui";
import { useMemo } from "react";

import { ConnectionSystemTypeMap } from "~/types/api";
import { ConnectionConfigurationResponse } from "~/types/api/models/ConnectionConfigurationResponse";

import type { ConnectionStatusData } from "../ConnectionStatusNotice";
import {
  Step,
  useAuthorizeIntegrationStep,
  useCreateIntegrationStep,
  useCreateMonitorStep,
  useLinkSystemStep,
} from "./hooks";

interface IntegrationSetupStepsProps {
  testData?: ConnectionStatusData;
  testIsLoading?: boolean;
  connectionOption?: ConnectionSystemTypeMap;
  connection?: ConnectionConfigurationResponse;
}

export const IntegrationSetupSteps = ({
  testData,
  testIsLoading,
  connectionOption,
  connection,
}: IntegrationSetupStepsProps) => {
  // Call hooks at the component level, not inside useMemo
  const addIntegrationStep = useCreateIntegrationStep();

  const authorizeIntegrationStep = useAuthorizeIntegrationStep({
    testData,
    testIsLoading,
    connectionOption,
  });

  const createMonitorStep = useCreateMonitorStep({
    testData,
    testIsLoading,
    connectionOption,
  });

  const linkSystemStep = useLinkSystemStep({
    testData,
    testIsLoading,
    connectionOption,
    connection,
  });

  // Use useMemo just to combine and filter the steps
  const steps = useMemo(() => {
    const allSteps: (Step | null)[] = [
      addIntegrationStep,
      authorizeIntegrationStep,
      createMonitorStep,
      linkSystemStep,
    ];

    // Filter out null steps (e.g., authorization step may be null if not required)
    return allSteps.filter((step): step is Step => step !== null);
  }, [
    addIntegrationStep,
    authorizeIntegrationStep,
    createMonitorStep,
    linkSystemStep,
  ]);

  const getCurrentStep = () => {
    const index = steps.findIndex((step) => step.state !== "finish");

    // If all steps are finished, return the index of the last step
    // instead of -1, to correctly highlight the last step as completed
    if (index === -1 && steps.length > 0) {
      return steps.length - 1;
    }

    return index;
  };

  const getStepStatus = () => {
    const incompleteStepIndex = steps.findIndex(
      (step) => step.state !== "finish",
    );

    // If all steps are complete, return 'finish'
    if (incompleteStepIndex === -1) {
      return "finish";
    }

    // Otherwise, return the status of the current incomplete step
    return steps[incompleteStepIndex].state;
  };

  // Add carbon icon to completed steps
  const stepsWithIcons = useMemo(() => {
    return steps.map((step) => ({
      ...step,
      icon:
        step.state === "finish" ? (
          <Icons.CheckmarkOutline size={24} />
        ) : undefined,
    }));
  }, [steps]);

  return (
    <Card title="Integration Setup">
      <Steps
        direction="vertical"
        current={getCurrentStep()}
        status={getStepStatus()}
        items={stepsWithIcons}
        size="small"
      />
    </Card>
  );
};
