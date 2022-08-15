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
        <Tab
          key={tab.label}
          data-testid={`tab-${tab.label}`}
          _selected={{
            fontWeight: "600",
            color: "complimentary.500",
            borderColor: "complimentary.500",
          }}
          fontWeight="500"
          color="gray.500"
        >
          {tab.label}
        </Tab>
      ))}
    </TabList>
    <TabPanels>
      {data.map((tab) => (
        <TabPanel px={0} key={tab.label} data-testid={`tab-panel-${tab.label}`}>
          {tab.content}
        </TabPanel>
      ))}
    </TabPanels>
  </Tabs>
);

export default DataTabs;
