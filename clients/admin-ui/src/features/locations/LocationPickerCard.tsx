import {
  Badge,
  Box,
  Button,
  Checkbox,
  CheckboxGroup,
  Flex,
  FormLabel,
  Spacer,
  Switch,
  VStack,
} from "@fidesui/react";
import { useState } from "react";

import QuestionTooltip from "~/features/common/QuestionTooltip";
import { Location, Selection } from "~/types/api";

const LocationPickerCard = ({
  title,
  locations,
  /** An array of Selections for ALL locations */
  selections,
  /** An updater for ALL locations */
  onChange,
}: {
  title: string;
  locations: Location[];
  selections: Array<Selection>;
  onChange: (selections: Array<Selection>) => void;
}) => {
  const [showRegulatedOnly, setShowRegulatedOnly] = useState(false);
  const filteredLocations = showRegulatedOnly
    ? locations.filter((l) => l.regulation?.length)
    : locations;

  // Filter to just the relevant "selections"
  const locationSelections = selections.filter((s) =>
    filteredLocations.find((l) => l.id === s.id)
  );
  const numSelected = locationSelections.filter((l) => l.selected).length;
  const allSelected = locationSelections.every((l) => l.selected);

  const handleToggleSelection = (id: string) => {
    const updated = selections.map((s) => {
      if (s.id === id) {
        return { ...s, selected: !s.selected };
      }
      return s;
    });
    onChange(updated);
  };

  const handleToggleAll = () => {
    const newSelected = !allSelected;
    const updated = selections.map((s) => {
      if (filteredLocations.find((l) => l.id === s.id)) {
        return { ...s, selected: newSelected };
      }
      return s;
    });
    onChange(updated);
  };

  return (
    <Box
      p={4}
      display="flex"
      alignItems="flex-start"
      gap="4px"
      borderRadius="4px"
      boxShadow="0px 1px 2px 0px rgba(0, 0, 0, 0.06), 0px 1px 3px 0px rgba(0, 0, 0, 0.1)"
      maxWidth="363px"
      fontSize="sm"
    >
      <VStack alignItems="flex-start" spacing={3} width="100%" height="100%">
        <Flex justifyContent="space-between" width="100%">
          <Checkbox
            fontSize="md"
            textTransform="capitalize"
            fontWeight="semibold"
            isChecked={allSelected}
            size="md"
            mr="2"
            onChange={handleToggleAll}
            colorScheme="complimentary"
          >
            {title}
          </Checkbox>

          <Flex alignItems="center" gap="8px">
            <Switch
              isChecked={showRegulatedOnly}
              size="sm"
              onChange={() => setShowRegulatedOnly(!showRegulatedOnly)}
              colorScheme="complimentary"
              id={`${title}-regulated`}
            />
            <FormLabel fontSize="sm" m={0} htmlFor={`${title}-regulated`}>
              Regulated
            </FormLabel>
            <QuestionTooltip label="Toggle on to see only locations in this region with privacy regulations supported by Fides" />
          </Flex>
        </Flex>
        {numSelected > 0 ? (
          <Badge colorScheme="purple" variant="solid" width="fit-content">
            {numSelected} selected
          </Badge>
        ) : null}
        <VStack paddingLeft="6" fontSize="sm" alignItems="start" spacing="2">
          <CheckboxGroup colorScheme="complimentary">
            {filteredLocations.map((location) => {
              const selection = locationSelections.find(
                (l) => l.id === location.id
              );
              return (
                <Flex key={location.id} alignItems="center" gap="8px">
                  <Checkbox
                    key={location.id}
                    isChecked={selection?.selected}
                    size="md"
                    fontWeight="500"
                    onChange={() => handleToggleSelection(location.id)}
                  >
                    {location.name}
                  </Checkbox>
                </Flex>
              );
            })}
          </CheckboxGroup>
        </VStack>
        <Spacer />
        <Button size="xs" variant="ghost">
          View more
        </Button>
      </VStack>
    </Box>
  );
};

export default LocationPickerCard;
