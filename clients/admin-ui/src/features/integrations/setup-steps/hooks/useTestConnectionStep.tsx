import { AntButton as Button } from "fidesui";

import { BaseStepHookParams, Step } from "./types";

interface TestConnectionStepParams extends BaseStepHookParams {
  onTestConnection?: () => void;
  needsAuthorization: boolean;
}

export const useTestConnectionStep = ({
  testData,
  testIsLoading,
  onTestConnection,
  needsAuthorization,
}: TestConnectionStepParams): Step => {
  const getConnectionDescription = () => {
    if (!testData?.timestamp) {
      return "Verify the integration connection";
    }
    if (testData.succeeded) {
      return "Connection verified successfully";
    }
    return "Connection test failed - check your credentials and try again";
  };

  const getConnectionState = (): Step["state"] => {
    if (testIsLoading) {
      return "process";
    }

    if (!testData?.timestamp) {
      return "wait";
    }

    return testData.succeeded ? "finish" : "error";
  };

  return {
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
  };
};
