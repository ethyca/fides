import { Button, Flex, Spacer, TabList, Tabs } from "fidesui";
import { useState } from "react";

import { FidesTab } from "~/features/common/DataTabs";
import {
  IntegrationTypeInfo,
  integrationTypeList,
} from "~/features/integrations/add-integration/allIntegrationTypes";
import IntegrationBox from "~/features/integrations/IntegrationBox";

type Props = {
  onCancel: () => void;
  onDetailClick: (type: IntegrationTypeInfo) => void;
  onConfigureClick: (type: IntegrationTypeInfo) => void;
};

const SelectIntegrationType = ({
  onCancel,
  onDetailClick,
  onConfigureClick,
}: Props) => {
  const [tabIndex, setTabIndex] = useState(0);

  const tabLabels = ["All", "Database", "Data Warehouse"];

  const currentTab = tabLabels[tabIndex];

  const filteredIntegrations = integrationTypeList.filter(
    (i) => currentTab === "All" || i.category === currentTab
  );

  return (
    <>
      <Tabs index={tabIndex} onChange={(i) => setTabIndex(i)} mb={4}>
        <TabList>
          {tabLabels.map((label) => (
            <FidesTab label={label} key={label} />
          ))}
        </TabList>
      </Tabs>
      <Flex direction="column">
        {filteredIntegrations.map((i) => (
          <IntegrationBox
            integration={i.placeholder}
            key={i.placeholder.key}
            onConfigureClick={() => onConfigureClick(i)}
            otherButtons={
              <Button onClick={() => onDetailClick(i)} variant="outline">
                Details
              </Button>
            }
          />
        ))}
      </Flex>
      <Flex>
        <Spacer />
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </Flex>
    </>
  );
};

export default SelectIntegrationType;
