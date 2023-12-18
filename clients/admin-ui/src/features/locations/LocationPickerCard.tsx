import { Flex, FormLabel, Switch, useDisclosure } from "@fidesui/react";
import { useState } from "react";

import PickerCard from "~/features/common/PickerCard";
import QuestionTooltip from "~/features/common/QuestionTooltip";
import { Location, Selection } from "~/types/api";

import SubgroupModal from "./SubgroupModal";

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
  const disclosure = useDisclosure();
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
    <>
      <PickerCard
        title={title}
        items={filteredLocations}
        selected={selected}
        onChange={handleChange}
        onViewMore={() => {
          disclosure.onOpen();
        }}
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
      <SubgroupModal
        locations={locations}
        isOpen={disclosure.isOpen}
        onClose={disclosure.onClose}
        selected={selected}
        // Rerender if a selection changes in this component so that the checkboxes
        // in the modal stay up to date
        key={`subgroup-modal-selected-${selected.length}`}
        onChange={handleChange}
      />
    </>
  );
};

export default LocationPickerCard;
