import { useDisclosure } from "@fidesui/react";
import { useState } from "react";

import PickerCard from "~/features/common/PickerCard";
import { Location, Selection } from "~/types/api";

import RegulatedToggle from "./RegulatedToggle";
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

  // We only show group level names here, i.e. "United States", which doesn't belong to
  // a larger group. So we don't show "California" here since it belongs to "United States"
  const locationsWithoutGroups = locations.filter((l) => !l.belongs_to?.length);
  const filteredLocations = showRegulatedOnly
    ? locationsWithoutGroups.filter((l) => l.regulation?.length)
    : locationsWithoutGroups;

  const handleChange = (newSelected: string[]) => {
    const updated = locations.map((location) => {
      if (newSelected.includes(location.id)) {
        return { ...location, selected: true };
      }
      return { ...location, selected: false };
    });
    onChange(updated);
  };

  const handlePropagateChildLocations = (parentSelections: Array<string>) => {
    const oldSelections = selected.filter((s) =>
      locationsWithoutGroups.find((l) => l.id === s)
    );
    const newSelections = new Set(parentSelections);

    // Set all children to true if parent was selected
    newSelections.forEach((newSelection) => {
      if (!oldSelections.includes(newSelection)) {
        locations.forEach((location) => {
          if (location.belongs_to?.includes(newSelection)) {
            newSelections.add(location.id);
          }
        });
      }
    });

    // Set all children to false if parent was deselected
    oldSelections.forEach((oldSelection) => {
      if (!newSelections.has(oldSelection)) {
        locations.forEach((location) => {
          if (location.belongs_to?.includes(oldSelection)) {
            newSelections.delete(location.id);
          }
        });
      }
    });

    handleChange(Array.from(newSelections));
  };

  const numSelected = selected.filter(
    (s) => !locationsWithoutGroups.find((l) => l.id === s)
  ).length;

  return (
    <>
      <PickerCard
        title={title}
        items={filteredLocations}
        selected={selected}
        onChange={handlePropagateChildLocations}
        onViewMore={() => {
          disclosure.onOpen();
        }}
        numSelected={numSelected}
        toggle={
          <RegulatedToggle
            id={`${title}-regulated`}
            isChecked={showRegulatedOnly}
            onChange={() => setShowRegulatedOnly(!showRegulatedOnly)}
          />
        }
      />
      <SubgroupModal
        locations={locations}
        isOpen={disclosure.isOpen}
        onClose={disclosure.onClose}
        selected={selected}
        onChange={handleChange}
        // Rerender if a selection changes in this component so that the checkboxes
        // in the modal stay up to date
        key={`subgroup-modal-selected-${selected.length}`}
      />
    </>
  );
};

export default LocationPickerCard;
