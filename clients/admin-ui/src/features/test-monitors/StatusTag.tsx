import { Alert, Tag, Typography } from "fidesui";

import { RunStatus } from "./types";

const { Text } = Typography;

const STEP_LABELS: Record<string, string> = {
  "creating-connection": "Creating connection…",
  "creating-monitor": "Creating monitor…",
  executing: "Triggering execution…",
};

const StatusTag = ({ status }: { status: RunStatus }) => {
  if (status.step === "idle") {
    return null;
  }
  if (status.step === "error") {
    return (
      <Alert
        type="error"
        message={status.message || "An error occurred"}
        showIcon
      />
    );
  }
  if (status.step === "done") {
    return (
      <Alert
        type="success"
        message={
          <span>
            Monitor executing.{" "}
            {status.executionId && (
              <>
                Execution ID: <Text code>{status.executionId}</Text>
              </>
            )}
          </span>
        }
        showIcon
      />
    );
  }
  return <Tag color="info">{STEP_LABELS[status.step]}</Tag>;
};

export default StatusTag;
