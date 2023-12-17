import { Continent, Location } from "~/types/api";

export const groupByContinent = (
  locations: Location[]
): Record<Continent, Location[]> => {
  const byContinent: Record<string, Location[]> = {};
  const allContinents = new Set(locations.map((l) => l.continent).sort());
  allContinents.forEach((continent) => {
    byContinent[continent] = locations.filter((l) => l.continent === continent);
  });
  return byContinent;
};

export const groupByBelongsTo = (
  locations: Location[]
): Record<string, Location[]> => {
  const byGroup: Record<string, Location[]> = {};
  const allGroups = new Set(
    locations
      .map((l) => l.belongs_to)
      .flat()
      .sort()
  );
  allGroups.forEach((group) => {
    if (group) {
      byGroup[group] = locations.filter((l) => l.belongs_to?.includes(group));
    }
  });
  return byGroup;
};
