import { BaseStepHookParams, Step } from "./types";

interface AuthorizeIntegrationStepParams extends BaseStepHookParams {}

export const useAuthorizeIntegrationStep = ({
  testData,
  connectionOption,
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
    title: "Authorize integration",
    description: <span>{getAuthorizationDescription()}</span>,
    state: testData?.authorized ? "finish" : "process",
  };
};
