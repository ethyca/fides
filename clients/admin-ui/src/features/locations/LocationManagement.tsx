import { Box, Button, SimpleGrid, useToast, VStack } from "@fidesui/react";
import _ from "lodash";
import { useMemo, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import SearchBar from "~/features/common/SearchBar";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { Location, LocationRegulationResponse, Selection } from "~/types/api";
import { isErrorResult } from "~/types/errors";

import LocationPickerCard from "./LocationPickerCard";
import { usePatchLocationsRegulationsMutation } from "./locations.slice";
import { groupByContinent } from "./transformations";

const SEARCH_FILTER = (location: Location, search: string) =>
  location.name?.toLocaleLowerCase().includes(search.toLocaleLowerCase());

const LocationManagement = ({ data }: { data: LocationRegulationResponse }) => {
  const toast = useToast();
  const [draftSelections, setDraftSelections] = useState<Array<Selection>>(
    data.locations ?? []
  );
  const [search, setSearch] = useState("");
  const [patchLocationsRegulationsMutationTrigger, { isLoading: isSaving }] =
    usePatchLocationsRegulationsMutation();

  const locationsByContinent = useMemo(() => {
    const filteredSearchLocations =
      data.locations?.filter((l) => SEARCH_FILTER(l, search)) ?? [];
    return groupByContinent(filteredSearchLocations);
  }, [data.locations, search]);

  const showSave = !_.isEqual(draftSelections, data.locations);

  const handleSave = async () => {
    const result = await patchLocationsRegulationsMutationTrigger({
      locations: draftSelections.map((s) => ({
        id: s.id,
        selected: s.selected,
      })),
      // no changes to regulations
      regulations: [],
    });
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          // TODO: "View regulations here"
          `Fides has automatically associated the relevant regulations with your location choices.`
        )
      );
    }
  };

  /** Allow changing a subset so it is easier to handle changes across continents */
  const handleDraftChange = (updatedSelections: Array<Selection>) => {
    const updated = draftSelections.map((draftSelection) => {
      const updatedSelection = updatedSelections.find(
        (s) => s.id === draftSelection.id
      );
      return updatedSelection ?? draftSelection;
    });
    setDraftSelections(updated);
  };

  return (
    <VStack alignItems="start" spacing={4}>
      <Box maxWidth="510px" width="100%">
        <SearchBar
          onChange={setSearch}
          placeholder="Search"
          search={search}
          onClear={() => setSearch("")}
          data-testid="search-bar"
        />
      </Box>
      <SimpleGrid columns={{ base: 1, md: 2, xl: 3 }} spacing={6}>
        {Object.entries(locationsByContinent).map(([continent, locations]) => (
          <LocationPickerCard
            key={continent}
            title={continent}
            locations={locations}
            selected={draftSelections
              .filter((s) => locations.find((l) => l.id === s.id) && s.selected)
              .map((s) => s.id)}
            onChange={handleDraftChange}
            view={search === "" ? "parents" : "all"}
          />
        ))}
      </SimpleGrid>
      {showSave ? (
        <Button
          colorScheme="primary"
          size="sm"
          onClick={handleSave}
          isLoading={isSaving}
          data-testid="save-btn"
        >
          Save
        </Button>
      ) : null}
    </VStack>
  );
};

export default LocationManagement;
