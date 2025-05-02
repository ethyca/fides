import {
  AntButton as Button,
  AntCard as Card,
  AntSteps as Steps,
} from "fidesui";
import { ReactNode, useMemo } from "react";

import { ConnectionSystemTypeMap } from "~/types/api";

import type { ConnectionStatusData } from "../ConnectionStatusNotice";

type StepState = "finish" | "process" | "wait" | "error";

interface IntegrationSetupStepsProps {
  testData?: ConnectionStatusData;
  testIsLoading?: boolean;
  onTestConnection?: () => void;
  onAuthorize?: () => void;
  connectionOption?: ConnectionSystemTypeMap;
}

interface Step {
  title: string;
  description: ReactNode;
  state: StepState;
}

export const IntegrationSetupSteps = ({
  testData,
  testIsLoading,
  onTestConnection,
  onAuthorize,
  connectionOption,
}: IntegrationSetupStepsProps) => {
  const getConnectionDescription = () => {
    if (!testData?.timestamp) {
      return "Verify the integration connection";
    }
    if (testData.succeeded) {
      return "Connection verified successfully";
    }
    return "Connection test failed - check your credentials and try again";
  };

  const getAuthorizationDescription = () => {
    if (!testData?.authorized) {
      return "Authorize access to your integration";
    }
    return "Integration authorized successfully";
  };

  const needsAuthorization =
    connectionOption?.authorization_required && !testData?.authorized;

  const getConnectionState = (): StepState => {
    if (testIsLoading) {
      return "process";
    }

    if (!testData?.timestamp) {
      return "wait";
    }

    return testData.succeeded ? "finish" : "error";
  };

  const steps = useMemo(() => {
    const baseSteps: Step[] = [
      {
        title: "Add Integration",
        description: "Configure and add your integration",
        state: "finish", // If we're viewing the integration, it's already added
      },
    ];

    if (connectionOption?.authorization_required) {
      baseSteps.push({
        title: "Authorize Integration",
        description: (
          <div className="flex items-center gap-2">
            <span>{getAuthorizationDescription()}</span>
            {onAuthorize && !testData?.authorized && (
              <Button
                size="small"
                onClick={onAuthorize}
                data-testid="step-authorize-integration-btn"
              >
                Authorize
              </Button>
            )}
          </div>
        ),
        state: testData?.authorized ? "finish" : "wait",
      });
    }

    return [
      ...baseSteps,
      {
        title: "Test Connection",
        description: (
          <div className="flex items-center gap-2">
            <span>{getConnectionDescription()}</span>
            {onTestConnection &&
              (!testData?.timestamp || !testData.succeeded) &&
              !needsAuthorization && (
                <Button
                  size="small"
                  onClick={onTestConnection}
                  loading={testIsLoading}
                  data-testid="step-test-connection-btn"
                >
                  Test
                </Button>
              )}
          </div>
        ),
        state: getConnectionState(),
      },
      {
        title: "Create Monitor",
        description: "Create and run a data monitor",
        state: "wait", // TODO: Add monitor creation status when available
      },
      {
        title: "Label Results",
        description: "Review and confirm the monitoring results",
        state: "wait", // TODO: Add labeling status when available
      },
      {
        title: "Test Datasets",
        description: "Validate the discovered datasets",
        state: "wait", // TODO: Add dataset validation status when available
      },
      {
        title: "Test DSR",
        description: "Run a test Data Subject Request",
        state: "wait", // TODO: Add DSR test status when available
      },
    ] as Step[];
  }, [
    onTestConnection,
    testIsLoading,
    onAuthorize,
    testData?.authorized,
    needsAuthorization,
    testData?.timestamp,
    testData?.succeeded,
  ]);

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
      />
    </Card>
  );
};
