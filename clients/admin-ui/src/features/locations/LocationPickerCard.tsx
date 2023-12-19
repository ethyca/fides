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
