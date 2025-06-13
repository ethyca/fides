import { AntTabs } from "fidesui";

interface DetectionResultFilterTabsProps {
  activeTabKey: string;
  onChange: (tab: string) => void;
  filterTabs: { label: string }[];
}

const DetectionResultFilterTabs = ({
  filterTabs,
  onChange,
  activeTabKey,
}: DetectionResultFilterTabsProps) => {
  return (
    <AntTabs
      items={filterTabs.map((tab) => ({
        key: tab.label,
        label: tab.label,
      }))}
      activeKey={activeTabKey}
      onChange={(tab) => onChange(tab as string)}
    />
  );
};
export default DetectionResultFilterTabs;
