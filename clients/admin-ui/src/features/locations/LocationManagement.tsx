import {
  AntButton,
  Box,
  SimpleGrid,
  Text,
  useDisclosure,
  useToast,
  VStack,
  WarningIcon,
} from "fidesui";
import _ from "lodash";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import ConfirmationModal from "~/features/common/modals/ConfirmationModal";
import SearchBar from "~/features/common/SearchBar";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { LocationRegulationResponse, Selection } from "~/types/api";
import { isErrorResult } from "~/types/errors";

import { REGULATIONS_ROUTE } from "../common/nav/v2/routes";
import ToastLink from "../common/ToastLink";
import LocationPickerCard from "./LocationPickerCard";
import { usePatchLocationsRegulationsMutation } from "./locations.slice";
import { groupLocationsByContinent } from "./transformations";

const LocationManagement = ({ data }: { data: LocationRegulationResponse }) => {
  const toast = useToast();
  const confirmationDisclosure = useDisclosure();
  const [draftSelections, setDraftSelections] = useState<Array<Selection>>(
    data.locations ?? [],
  );
  const [search, setSearch] = useState("");
  const [patchLocationsRegulationsMutationTrigger, { isLoading: isSaving }] =
    usePatchLocationsRegulationsMutation();

  const locationGroupsByContinent = useMemo(
    () =>
      groupLocationsByContinent(
        data.locations || [],
        data.location_groups || [],
      ),
    [data],
  );

  const showSave = !_.isEqual(draftSelections, data.locations);

  const router = useRouter();
  const goToRegulations = () => {
    router.push(REGULATIONS_ROUTE).then(() => {
      toast.closeAll();
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
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          <Text display="inline">
            Fides has automatically associated the relevant regulations with
            your location choices.{" "}
            <ToastLink onClick={goToRegulations}>
              View regulations here.
            </ToastLink>
          </Text>,
        ),
      );
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
      <ConfirmationModal
        isOpen={confirmationDisclosure.isOpen}
        onClose={confirmationDisclosure.onClose}
        onConfirm={() => {
          handleSave();
          confirmationDisclosure.onClose();
        }}
        title="Regulation updates"
        message="Modifications in your location settings may also affect your regulation settings to simplify management. You can override any Fides-initiated changes directly in the regulation settings."
        isCentered
        icon={<WarningIcon color="orange" />}
      />
      {showSave ? (
        <AntButton
          type="primary"
          onClick={confirmationDisclosure.onOpen}
          loading={isSaving}
          data-testid="save-btn"
        >
          Save
        </AntButton>
      ) : null}
    </VStack>
  );
};

export default LocationManagement;
