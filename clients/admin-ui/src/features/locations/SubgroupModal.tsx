import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Badge,
  Box,
  Button,
  ButtonGroup,
  Checkbox,
  Flex,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  SimpleGrid,
} from "@fidesui/react";
import { useMemo, useState } from "react";

import { usePicker } from "~/features/common/PickerCard";
import { Location } from "~/types/api";

import RegulatedToggle from "./RegulatedToggle";
import { getLocationNameFromId, groupByBelongsTo } from "./transformations";

const SubgroupModal = ({
  locations,
  isOpen,
  onClose,
  selected,
  onChange,
}: {
  locations: Location[];
  isOpen: boolean;
  onClose: () => void;
  selected: Array<string>;
  onChange: (newSelected: Array<string>) => void;
}) => {
  const [draftSelected, setDraftSelected] = useState(selected);
  const [showRegulatedOnly, setShowRegulatedOnly] = useState(false);

  const { filteredLocations, locationsByGroup } = useMemo(() => {
    const locationsWithGroups = locations.filter((l) => l.belongs_to?.length);
    const filtered = showRegulatedOnly
      ? locationsWithGroups.filter((l) => l.regulation?.length)
      : locationsWithGroups;
    return {
      locationsByGroup: groupByBelongsTo(filtered),
      filteredLocations: filtered,
    };
  }, [locations, showRegulatedOnly]);

  const { allSelected, handleToggleAll, handleToggleSelection } = usePicker({
    items: filteredLocations,
    selected: draftSelected,
    onChange: setDraftSelected,
  });

  // If a parent is selected, "United States", do not count it towards "num selected" but do
  // count its children
  const numSelected = draftSelected.filter(
    (s) => !Object.keys(locationsByGroup).includes(s)
  ).length;

  const handleApply = () => {
    const newSelected = new Set(draftSelected);
    // We also need to handle setting the group level location to true/false as needed
    Object.entries(locationsByGroup).forEach(([groupId, subLocations]) => {
      if (subLocations.every((l) => draftSelected.includes(l.id))) {
        newSelected.add(groupId);
      } else {
        newSelected.delete(groupId);
      }
    });
    onChange(Array.from(newSelected));
    onClose();
  };

  const continentName = locations[0].continent;
  const numSubgroups = Object.keys(locationsByGroup).length;

  return (
    <Modal size="2xl" isOpen={isOpen} onClose={onClose} isCentered>
      <ModalOverlay />
      <ModalContent data-testid="subgroup-modal">
        <ModalHeader
          fontSize="md"
          fontWeight="semibold"
          pt={5}
          paddingInline={6}
          pb={5}
          backgroundColor="gray.50"
          borderTopRadius="md"
          borderBottom="1px solid"
          borderColor="gray.200"
        >
          Select locations
        </ModalHeader>
        <ModalBody p={6}>
          <Flex justifyContent="space-between" mb={4}>
            <Box>
              <Checkbox
                colorScheme="complimentary"
                size="md"
                fontWeight={600}
                isChecked={allSelected}
                onChange={handleToggleAll}
                mr={3}
                data-testid="select-all"
              >
                {continentName}
              </Checkbox>
              <Badge
                colorScheme="purple"
                variant="solid"
                width="fit-content"
                data-testid="num-selected-badge"
              >
                {numSelected} selected
              </Badge>
            </Box>
            <RegulatedToggle
              id={`${continentName}-modal-regulated`}
              isChecked={showRegulatedOnly}
              onChange={() => setShowRegulatedOnly(!showRegulatedOnly)}
            />
          </Flex>
          {numSubgroups > 0 ? (
            <Accordion
              allowToggle
              allowMultiple
              // Opens all subgroups by default
              defaultIndex={[...Array(numSubgroups).keys()]}
            >
              {Object.entries(locationsByGroup).map(([group, subLocations]) => {
                const groupName = getLocationNameFromId(group, locations);
                return (
                  <AccordionItem
                    key={group}
                    data-testid={`${groupName}-accordion`}
                  >
                    <h2>
                      <AccordionButton>
                        <Box
                          as="span"
                          flex="1"
                          textAlign="left"
                          fontWeight={600}
                        >
                          {groupName}
                        </Box>
                        <AccordionIcon />
                      </AccordionButton>
                    </h2>
                    <AccordionPanel pb={4}>
                      <SimpleGrid columns={3} spacing={6}>
                        {subLocations.map((location) => (
                          <Checkbox
                            size="sm"
                            colorScheme="complimentary"
                            key={location.id}
                            isChecked={draftSelected.includes(location.id)}
                            onChange={() => handleToggleSelection(location.id)}
                            data-testid={`${location.name}-checkbox`}
                          >
                            {location.name}
                          </Checkbox>
                        ))}
                      </SimpleGrid>
                    </AccordionPanel>
                  </AccordionItem>
                );
              })}
            </Accordion>
          ) : (
            <SimpleGrid columns={3} spacing={6} paddingInline={4}>
              {filteredLocations.map((location) => (
                <Checkbox
                  size="sm"
                  colorScheme="complimentary"
                  key={location.id}
                  isChecked={draftSelected.includes(location.id)}
                  onChange={() => handleToggleSelection(location.id)}
                >
                  {location.name}
                </Checkbox>
              ))}
            </SimpleGrid>
          )}
        </ModalBody>
        <ModalFooter justifyContent="center">
          <ButtonGroup
            size="sm"
            display="flex"
            justifyContent="space-between"
            width="100%"
          >
            <Button flexGrow={1} variant="outline" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button
              flexGrow={1}
              colorScheme="primary"
              onClick={handleApply}
              data-testid="apply-btn"
            >
              Apply
            </Button>
          </ButtonGroup>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default SubgroupModal;
