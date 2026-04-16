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
import { LOCATIONS_ROUTE } from "~/features/common/nav/routes";
import SearchInput from "~/features/common/SearchInput";
import ToastLink from "~/features/common/ToastLink";
import {
  LocationRegulationBase,
  LocationRegulationResponse,
  Selection,
} from "~/types/api";
import { isErrorResult } from "~/types/errors";

import { usePatchLocationsRegulationsMutation } from "./locations.slice";
import RegulationPickerCard from "./RegulationPickerCard";
import { groupRegulationsByContinent } from "./transformations";

const SEARCH_FILTER = (regulation: LocationRegulationBase, search: string) =>
  regulation.name?.toLocaleLowerCase().includes(search.toLocaleLowerCase());

const RegulationManagement = ({
  data,
}: {
  data: LocationRegulationResponse;
}) => {
  const message = useMessage();
  const notification = useNotification();
  const modal = useModal();
  const [draftSelections, setDraftSelections] = useState<Array<Selection>>(
    data.regulations ?? [],
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
  const router = useRouter();
  const goToLocations = () => {
    router.push(LOCATIONS_ROUTE).then(() => {
      notification.destroy();
    });
  };

  const handleSave = async () => {
    const result = await patchLocationsRegulationsMutationTrigger({
      regulations: draftSelections.map((s) => ({
        id: s.id,
        selected: s.selected,
      })),
      // no changes to locations
      locations: [],
    });
    if (isErrorResult(result)) {
      message.error(getErrorMessage(result.error));
    } else {
      notification.success({
        message: "Regulation saved",
        description:
          "Fides has automatically associated the relevant locations with your regulation choices.",
        actions: <ToastLink onClick={goToLocations}>View locations</ToastLink>,
      });
    }
  };

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
    <VStack alignItems="start" spacing={4} data-testid="regulation-management">
      <Box maxWidth="510px" width="100%">
        <SearchInput
          onChange={setSearch}
          placeholder="Search"
          value={search}
          onClear={() => setSearch("")}
        />
      </Box>
      <SimpleGrid columns={{ base: 1, md: 2, xl: 3 }} spacing={6} width="100%">
        {Object.entries(regulationsByContinent).map(
          ([continent, regulations]) => {
            const selected = draftSelections
              .filter(
                (s) => regulations.find((r) => r.id === s.id) && s.selected,
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
              <RegulationPickerCard
                key={continent}
                title={continent}
                items={regulations}
                selected={selected}
                onChange={handleChange}
              />
            );
          },
        )}
      </SimpleGrid>
      {showSave && (
        <Button
          type="primary"
          onClick={() => {
            modal.confirm({
              title: "Location updates",
              content:
                "Modifications in your regulation settings may also affect your location settings to simplify management. You can override any Fides-initiated changes directly in the location settings.",
              centered: true,
              onOk: handleSave,
            });
          }}
          loading={isSaving}
          data-testid="save-btn"
        >
          Save
        </Button>
      )}
    </VStack>
  );
};

export default RegulationManagement;
