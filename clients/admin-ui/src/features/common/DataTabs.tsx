import {
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
  TabsProps,
} from "@fidesui/react";
import { ReactNode } from "react";

export type TabListBorder = "full-width" | "partial";

export interface TabData {
  label: string;
  content: ReactNode;
  isDisabled?: boolean;
}

interface Props {
  data: TabData[];
  border?: TabListBorder;
}

const DataTabs = ({
  data,
  border = "partial",
  ...other
}: Props & Omit<TabsProps, "children">) => (
  <Tabs colorScheme="complimentary" {...other}>
    <TabList width={border === "partial" ? "max-content" : undefined}>
      {data.map((tab, index) => (
        <Tab
          // eslint-disable-next-line react/no-array-index-key
          key={index}
          data-testid={`tab-${tab.label}`}
          _selected={{
            fontWeight: "600",
            color: "complimentary.500",
            borderColor: "complimentary.500",
          }}
          fontSize={other.fontSize}
          fontWeight="500"
          color="gray.500"
          isDisabled={tab.isDisabled || false}
        >
          {tab.label}
        </Tab>
      ))}
    </TabList>
    <TabPanels>
      {data.map((tab, index) => (
        // eslint-disable-next-line react/no-array-index-key
        <TabPanel px={0} key={index} data-testid={`tab-panel-${tab.label}`}>
          {tab.content}
        </TabPanel>
      ))}
    </TabPanels>
  </Tabs>
);

export default DataTabs;
