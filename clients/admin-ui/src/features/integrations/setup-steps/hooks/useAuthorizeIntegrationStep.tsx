import { AntButton as Button } from "fidesui";

import { BaseStepHookParams, Step } from "./types";

interface AuthorizeIntegrationStepParams extends BaseStepHookParams {
  onAuthorize?: () => void;
}

export const useAuthorizeIntegrationStep = ({
  testData,
  connectionOption,
  onAuthorize,
}: AuthorizeIntegrationStepParams): Step | null => {
  // Only return this step if authorization is required
  if (!connectionOption?.authorization_required) {
    return null;
  }

  const getAuthorizationDescription = () => {
    if (!testData?.authorized) {
      return "Authorize access to your integration";
    }
    return "Integration authorized successfully";
  };

  return {
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
  };
};
