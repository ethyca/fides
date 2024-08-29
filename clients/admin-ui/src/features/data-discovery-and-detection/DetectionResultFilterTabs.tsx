import DataTabsHeader from "~/features/common/DataTabsHeader";

interface DetectionResultFilterTabsProps {
  filterTabIndex: number;
  onChange: (index: number) => void;
  filterTabs: { label: string }[];
}

const DetectionResultFilterTabs = ({
  filterTabs,
  onChange,
  filterTabIndex,
}: DetectionResultFilterTabsProps) => {
  return (
    <DataTabsHeader
      border="full-width"
      mb={5}
      size="sm"
      data={filterTabs}
      borderWidth={1}
      index={filterTabIndex}
      onChange={onChange}
    />
  );
};
export default DetectionResultFilterTabs;
