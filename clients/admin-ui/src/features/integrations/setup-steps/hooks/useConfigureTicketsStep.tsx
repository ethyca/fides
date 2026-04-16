import { ConnectionType } from "~/types/api";

import { BaseStepHookParams, Step } from "./types";

export const useConfigureTicketsStep = ({
  connection,
}: BaseStepHookParams): Step | null => {
  if (connection?.connection_type !== ConnectionType.JIRA_TICKET) {
    return null;
  }

  const secrets = (connection as any)?.secrets as
    | Record<string, any>
    | undefined;
  const isComplete = !!(
    secrets?.project_key &&
    secrets?.issue_type &&
    secrets?.summary_template
  );

  return {
    title: "Configure tickets",
    content: isComplete ? (
      <span>Ticket configuration saved</span>
    ) : (
      <span>Set up project, issue type, and templates</span>
    ),
    state: isComplete ? "finish" : "process",
  };
};
