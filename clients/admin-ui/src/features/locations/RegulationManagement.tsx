import {
  Box,
  Button,
  SimpleGrid,
  useDisclosure,
  useToast,
  VStack,
  WarningIcon,
} from "@fidesui/react";
import _ from "lodash";
import { useMemo, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import ConfirmationModal from "~/features/common/modals/ConfirmationModal";
import PickerCard from "~/features/common/PickerCard";
import SearchBar from "~/features/common/SearchBar";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  LocationRegulationBase,
  LocationRegulationResponse,
  Selection,
} from "~/types/api";
import { isErrorResult } from "~/types/errors";

import { usePatchLocationsRegulationsMutation } from "./locations.slice";
import { groupRegulationsByContinent } from "./transformations";

const SEARCH_FILTER = (regulation: LocationRegulationBase, search: string) =>
  regulation.name?.toLocaleLowerCase().includes(search.toLocaleLowerCase());

const RegulationManagement = ({
  data,
}: {
  data: LocationRegulationResponse;
}) => {
  const toast = useToast();
  const confirmationDisclosure = useDisclosure();
  const [draftSelections, setDraftSelections] = useState<Array<Selection>>(
    data.regulations ?? []
  );
  const [search, setSearch] = useState("");
  const [patchLocationsRegulationsMutationTrigger, { isLoading: isSaving }] =
    usePatchLocationsRegulationsMutation();

  const regulationsByContinent = useMemo(() => {
    const filteredSearchLocations =
      data.regulations?.filter((l) => SEARCH_FILTER(l, search)) ?? [];
    return groupRegulationsByContinent(filteredSearchLocations);
  }, [data.regulations, search]);

  const showSave = !_.isEqual(draftSelections, data.regulations);

  const handleSave = async () => {
    const result = await patchLocationsRegulationsMutationTrigger({
      regulations: draftSelections.map((s) => ({
        id: s.id,
        selected: s.selected,
      })),
      // no changes to regulations
      locations: [],
    });
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          `Fides has automatically associated the relevant locations with your regulation choices.`
        )
      );
    }
  };

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
      <SimpleGrid columns={{ base: 1, md: 2, xl: 3 }} spacing={6} width="100%">
        {Object.entries(regulationsByContinent).map(
          ([continent, regulations]) => {
            const selected = draftSelections
              .filter(
                (s) => regulations.find((r) => r.id === s.id) && s.selected
              )
              .map((s) => s.id);
            const handleChange = (newSelected: string[]) => {
              const updatedSelections = regulations.map((regulation) => {
                if (newSelected.includes(regulation.id)) {
                  return { ...regulation, selected: true };
                }
                return { ...regulation, selected: false };
              });
              handleDraftChange(updatedSelections);
            };
            return (
              <PickerCard
                key={continent}
                title={continent}
                items={regulations}
                selected={selected}
                onChange={handleChange}
                numSelected={selected.length}
                indeterminate={[]}
              />
            );
          }
        )}
      </SimpleGrid>
      <ConfirmationModal
        isOpen={confirmationDisclosure.isOpen}
        onClose={confirmationDisclosure.onClose}
        onConfirm={() => {
          handleSave();
          confirmationDisclosure.onClose();
        }}
        title="Location updates"
        message="These updates to your regulation settings will automatically update your location settings."
        isCentered
        icon={<WarningIcon color="orange" />}
      />
      {showSave ? (
        <Button
          colorScheme="primary"
          size="sm"
          onClick={confirmationDisclosure.onOpen}
          isLoading={isSaving}
          data-testid="save-btn"
        >
          Save
        </Button>
      ) : null}
    </VStack>
  );
};

export default RegulationManagement;
