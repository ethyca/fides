import DataTabsHeader from "~/features/common/DataTabsHeader";

interface DetectionResultFilterTabsProps {
  tabIndex: number;
  onChange: (index: number) => void;
  tabs: { label: string }[];
}

const DetectionResultFilterTabs = ({
  tabs,
  onChange,
  tabIndex,
}: DetectionResultFilterTabsProps) => {
  return (
    <DataTabsHeader
      border="full-width"
      mb={5}
      size="sm"
      data={tabs}
      borderWidth={1}
      tabIndex={tabIndex}
      onChange={onChange}
    />
  );
};
export default DetectionResultFilterTabs;
