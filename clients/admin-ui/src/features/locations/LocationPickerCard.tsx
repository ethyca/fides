import { Flex, FormLabel, Switch } from "@fidesui/react";
import { useState } from "react";

import PickerCard from "~/features/common/PickerCard";
import QuestionTooltip from "~/features/common/QuestionTooltip";
import { Location, Selection } from "~/types/api";

const LocationPickerCard = ({
  title,
  locations,
  selected,
  onChange,
}: {
  title: string;
  locations: Location[];
  selected: Array<string>;
  onChange: (selections: Array<Selection>) => void;
}) => {
  const [showRegulatedOnly, setShowRegulatedOnly] = useState(false);

  const filteredLocations = showRegulatedOnly
    ? locations.filter((l) => l.regulation?.length)
    : locations;

  const handleChange = (newSelected: string[]) => {
    const updated = locations.map((location) => {
      if (newSelected.includes(location.id)) {
        return { ...location, selected: true };
      }
      return { ...location, selected: false };
    });
    onChange(updated);
  };

  return (
    <PickerCard
      title={title}
      items={filteredLocations}
      selected={selected}
      onChange={handleChange}
      toggle={
        <Flex alignItems="center" gap="8px">
          <Switch
            isChecked={showRegulatedOnly}
            size="sm"
            onChange={() => setShowRegulatedOnly(!showRegulatedOnly)}
            colorScheme="complimentary"
            id={`${title}-regulated`}
            data-testid="regulated-toggle"
          />
          <FormLabel fontSize="sm" m={0} htmlFor={`${title}-regulated`}>
            Regulated
          </FormLabel>
          <QuestionTooltip label="Toggle on to see only locations in this region with privacy regulations supported by Fides" />
        </Flex>
      }
    />
  );
};

export default LocationPickerCard;
