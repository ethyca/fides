import {
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
  TabsProps,
} from "@fidesui/react";
import { ReactNode } from "react";

interface TabData {
  label: string;
  content: ReactNode;
}

interface Props {
  data: TabData[];
}

const DataTabs = ({ data, ...other }: Props & Omit<TabsProps, "children">) => (
  <Tabs colorScheme="complimentary" {...other}>
    <TabList>
      {data.map((tab) => (
        <Tab key={tab.label} data-testid={`tab-${tab.label}`}>
          {tab.label}
        </Tab>
      ))}
    </TabList>
    <TabPanels>
      {data.map((tab) => (
        <TabPanel p={4} key={tab.label} data-testid={`tab-panel-${tab.label}`}>
          {tab.content}
        </TabPanel>
      ))}
    </TabPanels>
  </Tabs>
);

export default DataTabs;
