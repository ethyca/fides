import { useDisclosure } from "fidesui";
import { useState } from "react";

import PickerCard from "~/features/common/PickerCard";
import { Location, LocationGroup, Selection } from "~/types/api";

import RegulatedToggle from "./RegulatedToggle";
import SubgroupModal from "./SubgroupModal";
import { getCheckedStateLocationGroup, isRegulated } from "./transformations";

const SEARCH_FILTER = (data: { name?: string }, search: string) =>
  data.name?.toLocaleLowerCase().includes(search.toLocaleLowerCase());

const LocationPickerCard = ({
  title,
  groups,
  locations,
  selected: selectedLocations,
  onChange,
  search,
}: {
  title: string;
  groups: LocationGroup[];
  locations: Location[];
  selected: Array<string>;
  onChange: (selections: Array<Selection>) => void;
  search?: string;
}) => {
  const disclosure = useDisclosure();
  const [showRegulatedOnly, setShowRegulatedOnly] = useState(false);
  const showGroupsAndLocations = !!search?.length;
  const isGroupedView = groups.length > 0;

  let locationsForView = locations;
  if (groups.length) {
    locationsForView = groups;
  }
  if (showGroupsAndLocations) {
    locationsForView = [...locations, ...groups].sort((a, b) =>
      a.name.localeCompare(b.name),
    );
  }
  const regulatedLocations = showRegulatedOnly
    ? locationsForView.filter((l) => isRegulated(l, locations))
    : locationsForView;
  const filteredLocations = search
    ? regulatedLocations.filter((l) => SEARCH_FILTER(l, search))
    : regulatedLocations;

  const selectedGroups = groups
    .filter(
      (group) =>
        getCheckedStateLocationGroup({
          group,
          selected: selectedLocations,
          locations,
        }) === "checked",
    )
    .map((g) => g.id);
  const indeterminateGroups = groups
    .filter(
      (group) =>
        getCheckedStateLocationGroup({
          group,
          selected: selectedLocations,
          locations,
        }) === "indeterminate",
    )
    .map((g) => g.id);

  const selected = isGroupedView
    ? [...selectedGroups, ...selectedLocations]
    : selectedLocations;
  const numSelected = selectedLocations.length;

  const handleChange = (newSelected: string[]) => {
    const updated = locations.map((location) => {
      if (newSelected.includes(location.id)) {
        return { ...location, selected: true };
      }
      return { ...location, selected: false };
    });
    onChange(updated);
  };

  const handleGroupChange = (selections: string[]) => {
    const newSelected = new Set(selections);
    const oldSelected = new Set(selected);
    // Handle additions
    selections.forEach((s) => {
      if (!oldSelected.has(s)) {
        // If it's a group, we have to propagate
        if (groups.find((g) => g.id === s)) {
          locations
            .filter((l) => l.belongs_to?.includes(s))
            .forEach((l) => {
              newSelected.add(l.id);
            });
        }
      }
    });
    // Handle removals
    oldSelected.forEach((s) => {
      if (!newSelected.has(s)) {
        if (groups.find((g) => g.id === s)) {
          locations
            .filter((l) => l.belongs_to?.includes(s))
            .forEach((l) => {
              newSelected.delete(l.id);
            });
        }
      }
    });
    handleChange(Array.from(newSelected));
  };

  // Do not render the card if search ends up with no results
  if (filteredLocations.length === 0 && search) {
    return null;
  }

  return (
    <>
      <PickerCard
        title={title}
        items={filteredLocations}
        selected={selected}
        indeterminate={isGroupedView ? indeterminateGroups : []}
        onChange={handleGroupChange}
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
        groups={groups}
        locations={locations}
        isOpen={disclosure.isOpen}
        onClose={disclosure.onClose}
        selected={selectedLocations}
        onChange={handleChange}
        // Rerender if a selection changes in this component so that the checkboxes
        // in the modal stay up to date
        key={`subgroup-modal-selected-${selected.length}`}
      />
    </>
  );
};

export default LocationPickerCard;
