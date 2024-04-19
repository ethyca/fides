import { Badge, TabList, Tabs } from "@fidesui/react";
import { useState } from "react";

import { FidesTab } from "~/features/common/DataTabs";

export enum FirstLetterFilterValue {
  ALL,
  VOWEL,
  CONSONANT,
  NONE,
}

const FilterTabLabel = ({
  label,
  count,
  isActive,
}: {
  label: string;
  count: number;
  isActive?: boolean;
}) => (
  <>
    {count ? (
      <Badge
        fontSize={10}
        colorScheme={isActive ? "complimentary" : "gray"}
        variant="solid"
        mr={2}
        borderRadius={1000}
      >
        {count}
      </Badge>
    ) : null}
    <span>{label}</span>
  </>
);

const DiscoveryMonitorTabFilter = ({
  onFilterChange,
}: {
  onFilterChange: (filter: FirstLetterFilterValue) => void;
}) => {
  const [activeIndex, setActiveIndex] = useState<number>(0);

  const getFilterTypeByIndex = (i: number) => i as FirstLetterFilterValue;

  const handleChangeIndex = (newIndex: number) => {
    onFilterChange(getFilterTypeByIndex(newIndex));
    setActiveIndex(newIndex);
  };

  return (
    <Tabs
      index={activeIndex}
      onChange={handleChangeIndex}
      colorScheme="complimentary"
    >
      <TabList>
        {["All", "Vowel", "Consonant", "None"].map((filter, idx) => {
          const count = 3 - idx;
          return (
            <FidesTab
              // eslint-disable-next-line react/no-array-index-key
              key={idx}
              label={
                <FilterTabLabel
                  label={filter}
                  count={count}
                  isActive={idx === activeIndex}
                />
              }
              isDisabled={count === 0}
            />
          );
        })}
      </TabList>
    </Tabs>
  );
};
export default DiscoveryMonitorTabFilter;
