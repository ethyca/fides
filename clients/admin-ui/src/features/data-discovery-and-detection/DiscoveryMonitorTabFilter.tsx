import { TabList, Tabs, Tag, TagLabel } from "@fidesui/react";
import { useState } from "react";

import { FidesTab } from "~/features/common/DataTabs";

export enum FirstLetterFilterValue {
  ALL,
  VOWEL,
  CONSONANT,
  NONE,
}

const FilterTabLabel = ({ label, count }: { label: string; count: number }) => {
  return (
    <>
      <Tag size="sm" colorScheme="complimentary" mr={2}>
        <TagLabel>{count}</TagLabel>
      </Tag>
      <span>{label}</span>
    </>
  );
};

const DiscoveryMonitorTabFilter = ({
  onFilterChange,
}: {
  onFilterChange: (filter: FirstLetterFilterValue) => void;
}) => {
  const [index, setIndex] = useState<number>(0);

  const getFilterTypeByIndex = (i: number) => i as FirstLetterFilterValue;

  const handleChangeIndex = (newIndex: number) => {
    onFilterChange(getFilterTypeByIndex(newIndex));
    setIndex(newIndex);
  };

  return (
    <Tabs
      index={index}
      onChange={handleChangeIndex}
      colorScheme="complimentary"
    >
      <TabList>
        <FidesTab label={<FilterTabLabel label="All" count={1} />} />
        <FidesTab label={<FilterTabLabel label="Vowel" count={1} />} />
        <FidesTab label={<FilterTabLabel label="Consonant" count={1} />} />
        <FidesTab
          label={<FilterTabLabel label="None" count={1} />}
          isDisabled
        />
      </TabList>
    </Tabs>
  );
};
export default DiscoveryMonitorTabFilter;
