import { Text } from "@fidesui/react";
import React from "react";

type TestConnectionToastProps = {
  response: any;
};

const TestConnectionToast: React.FC<TestConnectionToastProps> = ({
  response
}) => (
  <>
    {response.data?.test_status === "succeeded" && (
        <Text>
          Connection test was successful
        </Text>
    )}
    {response.data?.test_status === "failed" && (
      <Text>
          Test failed: please check your connection info
      </Text>
    )}
  </>
);

export default TestConnectionToast;
