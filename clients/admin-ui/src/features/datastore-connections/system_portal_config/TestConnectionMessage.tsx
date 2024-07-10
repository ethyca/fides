import { Text } from "fidesui";
import React from "react";

type TestConnectionMessageProps = {
  status: "success" | "error";
};

const TestConnectionMessage = ({ status }: TestConnectionMessageProps) => (
  <>
    {status === "success" && <Text>Connection test was successful</Text>}
    {status === "error" && (
      <Text>Test failed: please check your connection info</Text>
    )}
  </>
);

export default TestConnectionMessage;
