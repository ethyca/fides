import { AntCard as Card, AntSteps as Steps } from "fidesui";
import { useMemo } from "react";

import { ConnectionSystemTypeMap } from "~/types/api";

import type { ConnectionStatusData } from "../ConnectionStatusNotice";
import {
  Step,
  useAuthorizeIntegrationStep,
  useCreateIntegrationStep,
  useCreateMonitorStep,
} from "./hooks";

interface IntegrationSetupStepsProps {
  testData?: ConnectionStatusData;
  testIsLoading?: boolean;
  onAuthorize?: () => void;
  connectionOption?: ConnectionSystemTypeMap;
}

export const IntegrationSetupSteps = ({
  testData,
  testIsLoading,
  onAuthorize,
  connectionOption,
}: IntegrationSetupStepsProps) => {
  // Call hooks at the component level, not inside useMemo
  const addIntegrationStep = useCreateIntegrationStep();

  const authorizeIntegrationStep = useAuthorizeIntegrationStep({
    testData,
    testIsLoading,
    connectionOption,
    onAuthorize,
  });

  const createMonitorStep = useCreateMonitorStep({
    testData,
    testIsLoading,
    connectionOption,
  });

  // Use useMemo just to combine and filter the steps
  const steps = useMemo(() => {
    const allSteps: (Step | null)[] = [
      addIntegrationStep,
      authorizeIntegrationStep,
      createMonitorStep,
    ];

    // Filter out null steps (e.g., authorization step may be null if not required)
    return allSteps.filter((step): step is Step => step !== null);
  }, [addIntegrationStep, authorizeIntegrationStep, createMonitorStep]);

  const getCurrentStep = () => {
    return steps.findIndex((step) => step.state !== "finish");
  };

  const getStepStatus = () => {
    const currentStep = getCurrentStep();
    if (currentStep === -1) {
      return "finish"; // All steps complete
    }

    return steps[currentStep].state;
  };

  return (
    <Card title="Integration Setup">
      <Steps
        direction="vertical"
        current={getCurrentStep()}
        status={getStepStatus()}
        items={steps}
        size="small"
      />
    </Card>
  );
};
