import {
  Button,
  ChakraBox as Box,
  ChakraSimpleGrid as SimpleGrid,
  ChakraVStack as VStack,
  useMessage,
  useModal,
  useNotification,
} from "fidesui";
import _ from "lodash";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import SearchInput from "~/features/common/SearchInput";
import {
  LocationRegulationResponse,
  PrivacyNoticeRegion,
  Selection,
} from "~/types/api";
import { isErrorResult } from "~/types/errors";

import { REGULATIONS_ROUTE } from "../common/nav/routes";
import ToastLink from "../common/ToastLink";
import LocationPickerCard from "./LocationPickerCard";
import { usePatchLocationsRegulationsMutation } from "./locations.slice";
import { groupLocationsByContinent } from "./transformations";

const LocationManagement = ({ data }: { data: LocationRegulationResponse }) => {
  const message = useMessage();
  const notification = useNotification();
  const modal = useModal();
  const [draftSelections, setDraftSelections] = useState<Array<Selection>>(
    data.locations?.filter((l) => l.id !== PrivacyNoticeRegion.GLOBAL) ?? [],
  );
  const [search, setSearch] = useState("");
  const [patchLocationsRegulationsMutationTrigger, { isLoading: isSaving }] =
    usePatchLocationsRegulationsMutation();

  const locationGroupsByContinent = useMemo(
    () =>
      groupLocationsByContinent(
        (data.locations || []).filter(
          (l) => l.id !== PrivacyNoticeRegion.GLOBAL,
        ),
        data.location_groups || [],
      ),
    [data],
  );

  const showSave = !_.isEqual(draftSelections, data.locations);

  const router = useRouter();
  const goToRegulations = () => {
    router.push(REGULATIONS_ROUTE).then(() => {
      notification.destroy();
    });
  };

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
      message.error(getErrorMessage(result.error));
    } else {
      notification.success({
        message: "Location saved",
        description:
          "Fides has automatically associated the relevant regulations with your location choices.",
        actions: (
          <ToastLink onClick={goToRegulations}>View regulations</ToastLink>
        ),
      });
    }
  };

  /** Allow changing a subset so it is easier to handle changes across continents */
  const handleDraftChange = (updatedSelections: Array<Selection>) => {
    const updated = draftSelections.map((draftSelection) => {
      const updatedSelection = updatedSelections.find(
        (s) => s.id === draftSelection.id,
      );
      return updatedSelection ?? draftSelection;
    });
    setDraftSelections(updated);
  };

  return (
    <VStack alignItems="start" spacing={4} data-testid="location-management">
      <Box maxWidth="510px" width="100%">
        <SearchInput
          onChange={setSearch}
          placeholder="Search"
          value={search}
          onClear={() => setSearch("")}
        />
      </Box>
      <SimpleGrid columns={{ base: 1, md: 2, xl: 3 }} spacing={6} width="100%">
        {Object.entries(locationGroupsByContinent).map(
          ([continent, continentData]) => (
            <LocationPickerCard
              key={continent}
              title={continent}
              groups={continentData.locationGroups}
              locations={continentData.locations}
              selected={draftSelections
                .filter(
                  (d) =>
                    continentData.locations.find((l) => l.id === d.id) &&
                    d.selected,
                )
                .map((d) => d.id)}
              onChange={handleDraftChange}
              search={search}
            />
          ),
        )}
      </SimpleGrid>
      {showSave ? (
        <Button
          type="primary"
          onClick={() => {
            modal.confirm({
              title: "Regulation updates",
              content:
                "Modifications in your location settings may also affect your regulation settings to simplify management. You can override any Fides-initiated changes directly in the regulation settings.",
              centered: true,
              onOk: handleSave,
            });
          }}
          loading={isSaving}
          data-testid="save-btn"
        >
          Save
        </Button>
      ) : null}
    </VStack>
  );
};

export default LocationManagement;
