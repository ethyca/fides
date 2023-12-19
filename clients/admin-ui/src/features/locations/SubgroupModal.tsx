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
    const filtered = showRegulatedOnly
      ? locations.filter((l) => l.regulation?.length)
      : locations;
    return {
      locationsByGroup: groupByBelongsTo(filtered),
      filteredLocations: filtered,
    };
  }, [locations, showRegulatedOnly]);

  const numSelected = draftSelected.length;
  const allSelected = filteredLocations.every((location) =>
    draftSelected.includes(location.id)
  );

  const handleCheck = (id: string) => {
    if (draftSelected.includes(id)) {
      setDraftSelected(draftSelected.filter((s) => s !== id));
    } else {
      setDraftSelected([...draftSelected, id]);
    }
  };

  const handleCheckAll = () => {
    if (allSelected) {
      setDraftSelected([]);
    } else {
      setDraftSelected(filteredLocations.map((l) => l.id));
    }
  };

  const handleApply = () => {
    onChange(draftSelected);
    onClose();
  };

  const continentName = locations[0].continent;
  const numSubgroups = Object.keys(locationsByGroup).length;

  return (
    <Modal size="2xl" isOpen={isOpen} onClose={onClose} isCentered>
      <ModalOverlay />
      <ModalContent>
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
                onChange={handleCheckAll}
                mr={3}
              >
                {continentName}
              </Checkbox>
              {numSelected > 0 ? (
                <Badge
                  colorScheme="purple"
                  variant="solid"
                  width="fit-content"
                  data-testid="num-selected-badge"
                >
                  {numSelected} selected
                </Badge>
              ) : null}
            </Box>
            <RegulatedToggle
              id={`${continentName}-modal-regulated`}
              isChecked={showRegulatedOnly}
              onChange={() => setShowRegulatedOnly(!showRegulatedOnly)}
            />
          </Flex>
          <Accordion
            allowToggle
            allowMultiple
            defaultIndex={[...Array(numSubgroups).keys()]}
          >
            {Object.entries(locationsByGroup).map(([group, subLocations]) => (
              <AccordionItem key={group}>
                <h2>
                  <AccordionButton>
                    <Box as="span" flex="1" textAlign="left" fontWeight={600}>
                      {getLocationNameFromId(group, locations)}
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
                        onChange={() => handleCheck(location.id)}
                      >
                        {location.name}
                      </Checkbox>
                    ))}
                  </SimpleGrid>
                </AccordionPanel>
              </AccordionItem>
            ))}
          </Accordion>
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
            <Button flexGrow={1} colorScheme="primary" onClick={handleApply}>
              Apply
            </Button>
          </ButtonGroup>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default SubgroupModal;
