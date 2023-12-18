import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  Button,
  ButtonGroup,
  Checkbox,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  SimpleGrid,
} from "@fidesui/react";
import { useMemo } from "react";

import { Location } from "~/types/api";

import { getLocationNameFromId, groupByBelongsTo } from "./transformations";

const SubgroupModal = ({
  locations,
  isOpen,
  onClose,
}: {
  locations: Location[];
  isOpen: boolean;
  onClose: () => void;
}) => {
  const locationsByGroup = useMemo(
    () => groupByBelongsTo(locations),
    [locations]
  );

  return (
    <Modal size="2xl" isOpen={isOpen} onClose={onClose} isCentered>
      <ModalOverlay />
      <ModalContent>
        <ModalHeader
          fontSize="md"
          fontWeight="semibold"
          pt={6}
          paddingInline={6}
          pb={3}
          backgroundColor="gray.50"
          borderTopRadius="md"
          borderBottom="1px solid"
          borderColor="gray.200"
        >
          Select locations
        </ModalHeader>
        <ModalBody p={6}>
          <Accordion allowToggle allowMultiple>
            {Object.entries(locationsByGroup).map(([group, subLocations]) => (
              <AccordionItem key={group}>
                <h2>
                  <AccordionButton>
                    <Box as="span" flex="1" textAlign="left">
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
            <Button flexGrow={1} colorScheme="primary">
              Apply
            </Button>
          </ButtonGroup>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default SubgroupModal;
