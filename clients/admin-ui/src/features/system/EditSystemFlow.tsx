import { VStack } from "@fidesui/react";

import SystemFormTabs from "./SystemFormTabs";

const EditSystemFlow = () => {
  return (
    <VStack alignItems="stretch" flex="1" gap="18px" maxWidth="70vw">
      <SystemFormTabs />
    </VStack>
  );
};

export default EditSystemFlow;
