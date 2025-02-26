import { Text } from "fidesui";
import React from "react";

type TestConnectionMessageProps = {
  status: "success" | "error";
};

const TestConnectionMessage = ({ status }: TestConnectionMessageProps) => (
  <>
    {status === "success" && (
      <Text data-testid="toast-success-msg">
        Connection test was successful
      </Text>
    )}
    {status === "error" && (
      <Text data-testid="toast-error-msg">
        Test failed: please check your connection info
      </Text>
    )}
  </>
);

export default TestConnectionMessage;
