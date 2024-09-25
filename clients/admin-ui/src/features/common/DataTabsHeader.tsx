import { TabList, Tabs, TabsProps } from "fidesui";

import { FidesTab, TabData, TabListBorder } from "~/features/common/DataTabs";

interface DataTabsHeaderProps {
  data: Pick<TabData, "label" | "isDisabled">[];
  border?: TabListBorder;
  borderWidth?: TabsProps["borderWidth"];
}

const DataTabsHeader = ({
  data,
  border = "partial",
  borderWidth = 2,
  ...other
}: DataTabsHeaderProps & Omit<TabsProps, "children">) => (
  <Tabs colorScheme="complimentary" {...other}>
    <TabList
      width={border === "partial" ? "max-content" : undefined}
      borderBottomWidth={borderWidth}
    >
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
