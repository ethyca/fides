import {
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  TabProps,
  Tabs,
  TabsProps,
} from "fidesui";
import { ReactNode } from "react";

export type TabListBorder = "full-width" | "partial";

export const FidesTab = ({
  label,
  isDisabled,
  ...other
}: {
  label: string | ReactNode;
  isDisabled?: boolean;
} & TabProps) => (
  <Tab
    data-testid={`tab-${label}`}
    _selected={{
      fontWeight: "600",
      color: "complimentary.500",
      borderColor: "complimentary.500",
    }}
    fontSize={other.fontSize}
    fontWeight="500"
    color="gray.500"
    isDisabled={isDisabled || false}
  >
    {label}
  </Tab>
);

export interface TabData {
  label: string;
  content: ReactNode | JSX.Element;
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
      {data.map((tab) => (
        <FidesTab
          key={tab.label}
          label={tab.label}
          isDisabled={tab.isDisabled}
          fontSize={other.fontSize}
        />
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
