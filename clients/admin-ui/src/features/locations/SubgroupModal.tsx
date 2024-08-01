import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  Checkbox,
  Modal,
  ModalBody,
  ModalContent,
  ModalOverlay,
  SimpleGrid,
} from "fidesui";
import { useMemo, useState } from "react";

import { usePicker } from "~/features/common/hooks/usePicker";
import { Location, LocationGroup } from "~/types/api";

import { Footer, Header, HeaderCheckboxRow } from "./modal";
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
    (s) => !Object.keys(locationsByGroup).includes(s),
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
  const subgroups = Object.keys(locationsByGroup);
  // If there are only "Others" do not render the group view
  const isGroupedView = !(subgroups.length === 1 && subgroups[0] === "Other");

  return (
    <Modal size="2xl" isOpen={isOpen} onClose={onClose} isCentered>
      <ModalOverlay />
      <ModalContent data-testid="subgroup-modal">
        <Header title="Select locations" />
        <ModalBody p={6} maxHeight="70vh" overflowY="auto">
          <HeaderCheckboxRow
            title={continentName}
            allSelected={allSelected}
            onToggleAll={handleToggleAll}
            numSelected={numSelected}
          >
            <RegulatedToggle
              id={`${continentName}-modal-regulated`}
              isChecked={showRegulatedOnly}
              onChange={() => setShowRegulatedOnly(!showRegulatedOnly)}
            />
          </HeaderCheckboxRow>
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
                            fontWeight="semibold"
                            fontSize="sm"
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
                },
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
        <Footer onApply={handleApply} onClose={onClose} />
      </ModalContent>
    </Modal>
  );
};

export default SubgroupModal;
