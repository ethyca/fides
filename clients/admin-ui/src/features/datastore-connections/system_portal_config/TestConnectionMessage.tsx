import { Text } from "fidesui";
import React from "react";

type TestConnectionMessageProps = {
  status: "success" | "error";
  failure_reason?: string;
};

const TestConnectionMessage = ({
  status,
  failure_reason,
}: TestConnectionMessageProps) => {
  if (status === "error") {
    let description = "Connection test failed.";
    if (failure_reason) {
      description += ` ${failure_reason}`;
    }
    return <Text data-testid="toast-error-msg">{description}</Text>;
  }

  return (
    <Text data-testid="toast-success-msg">Connection test was successful</Text>
  );
};

export default TestConnectionMessage;
