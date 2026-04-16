import { ConnectionType } from "~/types/api";

import { BaseStepHookParams, Step } from "./types";

interface AuthorizeIntegrationStepParams extends BaseStepHookParams {}

export const useAuthorizeIntegrationStep = ({
  testData,
  connection,
  connectionOption,
}: AuthorizeIntegrationStepParams): Step | null => {
  const isJiraTicket =
    connection?.connection_type === ConnectionType.JIRA_TICKET;

  if (!connectionOption?.authorization_required && !isJiraTicket) {
    return null;
  }

  const getAuthorizationDescription = () => {
    if (!testData?.authorized) {
      return isJiraTicket
        ? "Authorize Fides to connect to your Jira instance"
        : "Authorize access to your integration";
    }
    return "Integration authorized successfully";
  };

  return {
    title: "Authorize integration",
    content: <span>{getAuthorizationDescription()}</span>,
    state: testData?.authorized ? "finish" : "process",
  };
};
