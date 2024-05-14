import { VStack } from "fidesui";

import SystemFormTabs from "./SystemFormTabs";

const EditSystemFlow = ({ initialTabIndex = 0 }) => (
  <VStack alignItems="stretch" flex="1" gap="18px" maxWidth="70vw">
    <SystemFormTabs initialTabIndex={initialTabIndex} />
  </VStack>
);

export default EditSystemFlow;
