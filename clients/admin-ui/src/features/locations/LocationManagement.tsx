import { Box } from "@fidesui/react";
import { useMemo } from "react";

import { Continent, Location } from "~/types/api";

import LocationPickerCard from "./LocationPickerCard";
import { groupByContinent } from "./transformations";

const mockLocation = (override?: Partial<Location>) => {
  const base: Location = {
    id: "US-VA",
    name: "Virginia",
    belongs_to: ["United States"],
    continent: Continent.NORTH_AMERICA,
    regulation: ["usva"],
    selected: false,
  };
  if (override) {
    return { ...base, ...override };
  }
  return base;
};
const data = [mockLocation()];

const LocationManagement = () => {
  const locationsByContinent = useMemo(() => groupByContinent(data), []);
  return (
    <Box>
      {Object.entries(locationsByContinent).map(([continent, locations]) => (
        <LocationPickerCard
          key={continent}
          title={continent}
          locations={locations}
        />
      ))}
    </Box>
  );
};

export default LocationManagement;
