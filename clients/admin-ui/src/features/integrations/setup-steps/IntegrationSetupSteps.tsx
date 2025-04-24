import {
  AntButton as Button,
  AntCard as Card,
  AntSteps as Steps,
} from "fidesui";
import { useMemo } from "react";

import type { ConnectionStatusData } from "../ConnectionStatusNotice";

interface IntegrationSetupStepsProps {
  testData?: ConnectionStatusData;
  testIsLoading?: boolean;
  onTestConnection?: () => void;
}

export const IntegrationSetupSteps = ({
  testData,
  testIsLoading,
  onTestConnection,
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

  const steps = useMemo(() => {
    return [
      {
        title: "Add Integration",
        description: "Configure and add your integration",
      },
      {
        title: "Test Connection",
        description: (
          <div className="flex items-center gap-2">
            <span>{getConnectionDescription()}</span>
            {onTestConnection &&
              (!testData?.timestamp || !testData.succeeded) && (
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
      },
      {
        title: "Create Monitor",
        description: "Create and run a data monitor",
      },
      {
        title: "Label Results",
        description: "Review and confirm the monitoring results",
      },
      {
        title: "Test Datasets",
        description: "Validate the discovered datasets",
      },
      {
        title: "Test DSR",
        description: "Run a test Data Subject Request",
      },
    ];
  }, [onTestConnection, testIsLoading]);

  const getTestConnectionStatus = () => {
    if (testIsLoading) {
      return "process";
    }
    if (!testData?.timestamp) {
      return "wait";
    }
    return testData.succeeded ? "finish" : "error";
  };

  return (
    <Card title="Integration Setup">
      <Steps
        direction="vertical"
        current={1}
        status={getTestConnectionStatus()}
        items={steps}
      />
    </Card>
  );
};
