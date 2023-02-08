import { Box } from "@fidesui/react";
import { useState } from "react";

import DataTabs, { type TabData } from "~/features/common/DataTabs";

/**
 * This is named very similarly to DescribeSystemStep because both components
 * do very similar things. In the future, these two flows may be consolidated,
 * and at that point we should also consolidate the components.
 */
const DescribeSystem = () => {
  const [tabIndex, setTabIndex] = useState(0);
  const tabData: TabData[] = [
    {
      label: "System information",
      content: <Box>system info</Box>,
    },
    {
      label: "Privacy declarations",
      content: <Box>privacy declaration</Box>,
      //   isDisabled: !activeSystem,
    },
  ];

  return (
    <Box>
      <DataTabs
        data={tabData}
        data-testid="system-tabs"
        index={tabIndex}
        isLazy
        onChange={setTabIndex}
      />
    </Box>
  );
};

export default DescribeSystem;
