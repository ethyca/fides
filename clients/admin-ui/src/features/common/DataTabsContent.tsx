import { TabPanel, TabPanels, Tabs, TabsProps } from "fidesui";

import { TabData } from "~/features/common/DataTabs";

interface DataTabsContentProps {
  data: TabData[];
}

const DataTabsContent = ({
  data,
  ...other
}: DataTabsContentProps & Omit<TabsProps, "children">) => (
  <Tabs {...other}>
    <TabPanels>
      {data.map((tab) => (
        <TabPanel px={0} key={tab.label} data-testid={`tab-panel-${tab.label}`}>
          {tab.content}
        </TabPanel>
      ))}
    </TabPanels>
  </Tabs>
);
export default DataTabsContent;
