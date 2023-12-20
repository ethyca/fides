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
import { Location, LocationGroup } from "~/types/api";

import RegulatedToggle from "./RegulatedToggle";
import { groupByBelongsTo } from "./transformations";

const SubgroupModal = ({
  groups,
  locations,
  isOpen,
  onClose,
  selected,
  onChange,
}: {
  groups: LocationGroup[];
  locations: Location[];
  isOpen: boolean;
  onClose: () => void;
  selected: Array<string>;
  onChange: (newSelected: Array<string>) => void;
}) => {
  const [draftSelected, setDraftSelected] = useState(selected);
  const [showRegulatedOnly, setShowRegulatedOnly] = useState(false);

  const { filteredLocations, locationsByGroup } = useMemo(() => {
    const filtered = showRegulatedOnly
      ? locations.filter((l) => l.regulation?.length)
      : locations;
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
  const isGroupedView = numSubgroups > 0;

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
        <ModalBody p={6} maxHeight="70vh" overflowY="auto">
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
          {isGroupedView ? (
            <Accordion allowToggle allowMultiple>
              {Object.entries(locationsByGroup).map(
                ([groupId, subLocations]) => {
                  const group = groups.find((g) => groupId === g.id);
                  const groupName = group ? group.name : groupId;
                  return (
                    <AccordionItem
                      key={groupId}
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
                              onChange={() =>
                                handleToggleSelection(location.id)
                              }
                              data-testid={`${location.name}-checkbox`}
                            >
                              {location.name}
                            </Checkbox>
                          ))}
                        </SimpleGrid>
                      </AccordionPanel>
                    </AccordionItem>
                  );
                }
              )}
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
                  data-testid={`${location.name}-checkbox`}
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
