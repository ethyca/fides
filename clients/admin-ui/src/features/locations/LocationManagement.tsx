import { SimpleGrid } from "@fidesui/react";
import { useMemo, useState } from "react";

import { LocationRegulationResponse, Selection } from "~/types/api";

import LocationPickerCard from "./LocationPickerCard";
import { groupByContinent } from "./transformations";

// const mockLocation = (override?: Partial<Location>) => {
//   const base: Location = {
//     id: "US-VA",
//     name: "Virginia",
//     belongs_to: ["United States"],
//     continent: Continent.NORTH_AMERICA,
//     regulation: ["usva"],
//     selected: false,
//   };
//   if (override) {
//     return { ...base, ...override };
//   }
//   return base;
// };

const LocationManagement = ({ data }: { data: LocationRegulationResponse }) => {
  const [draftSelections, setDraftSelections] = useState<Array<Selection>>(
    data.locations ?? []
  );
  const locationsByContinent = useMemo(
    () => groupByContinent(data.locations ?? []),
    [data]
  );

  return (
    <SimpleGrid columns={{ base: 1, md: 2, xl: 3 }} spacing={6}>
      {Object.entries(locationsByContinent).map(([continent, locations]) => (
        <LocationPickerCard
          key={continent}
          title={continent}
          locations={locations}
          selections={draftSelections}
          onChange={setDraftSelections}
        />
      ))}
    </SimpleGrid>
  );
};

export default LocationManagement;
