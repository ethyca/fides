import {
  Continent,
  Location,
  LocationGroup,
  LocationRegulationBase,
} from "~/types/api";

export const groupLocationsByContinent = (
  locations: Location[],
  locationGroups: LocationGroup[],
): Record<
  Continent,
  { locations: Location[]; locationGroups: LocationGroup[] }
> => {
  const byContinent: Record<
    string,
    { locations: Location[]; locationGroups: LocationGroup[] }
  > = {};
  const allContinents = new Set(locations.map((l) => l.continent).sort());
  allContinents.forEach((continent) => {
    byContinent[continent] = {
      locationGroups: locationGroups
        .filter((l) => l.continent === continent)
        .sort((a, b) => a.name.localeCompare(b.name)),
      locations: locations
        .filter((l) => l.continent === continent)
        .sort((a, b) => a.name.localeCompare(b.name)),
    };
  });

  return byContinent;
};

export const groupRegulationsByContinent = (
  regulations: LocationRegulationBase[],
): Record<Continent, LocationRegulationBase[]> => {
  const byContinent: Record<string, LocationRegulationBase[]> = {};
  const allContinents = new Set(regulations.map((r) => r.continent).sort());
  allContinents.forEach((continent) => {
    byContinent[continent] = regulations
      .filter((r) => r.continent === continent)
      .sort((a, b) => a.name.localeCompare(b.name));
  });
  return byContinent;
};

export const groupByBelongsTo = (
  locations: Location[],
): Record<string, Location[]> => {
  const byGroup: Record<string, Location[]> = {};
  const allGroups = new Set(
    locations
      .map((l) => l.belongs_to)
      .flat()
      .sort(),
  );
  allGroups.forEach((group) => {
    if (group) {
      byGroup[group] = locations
        .filter((l) => l.belongs_to?.includes(group))
        .sort((a, b) => a.name.localeCompare(b.name));
    }
  });
  // Manually set all other locations that do not belong to a group to "Other"
  const other = locations.filter(
    (l) => !l.belongs_to || l.belongs_to.length === 0,
  );
  if (other.length) {
    byGroup.Other = other;
  }
  return byGroup;
};

export const isRegulated = (
  locationOrGroup: Location | LocationGroup,
  locations: Location[],
) => {
  if (locationOrGroup.regulation?.length) {
    return true;
  }
  const locationsInGroup = locations.filter((l) =>
    l.belongs_to?.includes(locationOrGroup.id),
  );
  return locationsInGroup.some((l) => l.regulation?.length);
};

export const getCheckedStateLocationGroup = ({
  group,
  selected,
  locations,
}: {
  group: LocationGroup;
  selected: string[];
  locations: Location[];
}): "checked" | "unchecked" | "indeterminate" => {
  const locationsInGroup = locations.filter((l) =>
    l.belongs_to?.includes(group.id),
  );
  if (locationsInGroup.length === 0) {
    return "unchecked";
  }
  if (locationsInGroup.every((l) => selected.includes(l.id))) {
    return "checked";
  }
  if (locationsInGroup.every((l) => !selected.includes(l.id))) {
    return "unchecked";
  }
  return "indeterminate";
};
