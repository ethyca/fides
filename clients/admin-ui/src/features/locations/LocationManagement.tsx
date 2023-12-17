import { Box, SimpleGrid, VStack } from "@fidesui/react";
import { useMemo, useState } from "react";

import SearchBar from "~/features/common/SearchBar";
import { Location, LocationRegulationResponse, Selection } from "~/types/api";

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

const SEARCH_FILTER = (location: Location, search: string) =>
  location.name?.toLocaleLowerCase().includes(search.toLocaleLowerCase()) ||
  location.continent?.toLocaleLowerCase().includes(search.toLocaleLowerCase());

const LocationManagement = ({ data }: { data: LocationRegulationResponse }) => {
  const [draftSelections, setDraftSelections] = useState<Array<Selection>>(
    data.locations ?? []
  );
  const [search, setSearch] = useState("");

  const locationsByContinent = useMemo(() => {
    const filteredSearchLocations =
      data.locations?.filter((l) => SEARCH_FILTER(l, search)) ?? [];
    return groupByContinent(filteredSearchLocations);
  }, [data.locations, search]);

  return (
    <VStack alignItems="start" spacing={4}>
      <Box maxWidth="510px" width="100%">
        <SearchBar
          onChange={setSearch}
          placeholder="Search"
          search={search}
          onClear={() => setSearch("")}
        />
      </Box>
      <SimpleGrid columns={{ base: 1, md: 2, xl: 3 }} spacing={6} width="100%">
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
    </VStack>
  );
};

export default LocationManagement;
