import { TabList, Tabs, TabsProps } from "fidesui";

import { FidesTab, TabData, TabListBorder } from "~/features/common/DataTabs";

interface DataTabsHeaderProps {
  data: Pick<TabData, "label" | "isDisabled">[];
  border?: TabListBorder;
}

const DataTabsHeader = ({
  data,
  border = "partial",
  ...other
}: DataTabsHeaderProps & Omit<TabsProps, "children">) => (
  <Tabs colorScheme="complimentary" {...other}>
    <TabList width={border === "partial" ? "max-content" : undefined}>
      {data.map((tab) => (
        <FidesTab
          key={tab.label}
          label={tab.label}
          data-testid={tab.label}
          isDisabled={tab.isDisabled}
          fontSize={other.fontSize}
        />
      ))}
    </TabList>
  </Tabs>
);
export default DataTabsHeader;
