import { Text } from "fidesui";

import ConnectedCircle from "../common/ConnectedCircle";
import { formatDate } from "../common/utils";

type TestDataProps = {
  succeeded?: boolean;
  timestamp: string | number;
};

const TestData: React.FC<TestDataProps> = ({ succeeded, timestamp }) => {
  const date = timestamp ? formatDate(timestamp) : "";
  const testText = timestamp
    ? `Last tested on ${date}`
    : "This connection has not been tested yet";

  return (
    <>
      <ConnectedCircle connected={succeeded} />
      <Text
        color="gray.500"
        fontSize="xs"
        fontWeight="semibold"
        lineHeight="16px"
        ml="10px"
      >
        {testText}
      </Text>
    </>
  );
};

export default TestData;
