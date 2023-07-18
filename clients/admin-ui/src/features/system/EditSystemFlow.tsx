import { VStack } from "@fidesui/react";

import SystemFormTabs from "./SystemFormTabs";

const EditSystemFlow = ({ initialTabIndex = 0 }) => {
  return (
    <VStack alignItems="stretch" flex="1" gap="18px" maxWidth="70vw">
      <SystemFormTabs initialTabIndex={initialTabIndex} />
    </VStack>
  );
};

export default EditSystemFlow;
