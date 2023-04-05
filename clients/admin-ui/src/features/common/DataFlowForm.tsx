import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  Flex,
  Heading,
  Tag,
  Text,
  Button,
} from "@fidesui/react";
import { System } from "~/types/api/models/System";
import { DataFlow } from "~/types/api";
import React from "react";
import { GearLightIcon } from "common/Icon";

type DataFlowAccordionItemProps = {
  isIngress?: boolean;
  systems: DataFlow[];
};

const DataFlowAccordionItem = ({
  systems,
  isIngress,
}: DataFlowAccordionItemProps) => {
  const flowType = isIngress ? "Source" : "Destination";

  return (
    <AccordionItem>
      <AccordionButton>
        <Box
          display="flex"
          alignItems="center"
          justifyContent="space-between"
          flex={1}
          textAlign="left"
        >
          <Flex>
            <Heading as="h4" size="xs" fontWeight="medium" mr={4}>
              {flowType}
            </Heading>
            <Tag
              ml={2}
              backgroundColor="primary.400"
              borderRadius="6px"
              color="white"
            >
              {systems.length}
            </Tag>
          </Flex>
          <AccordionIcon />
        </Box>
      </AccordionButton>
      <AccordionPanel backgroundColor="gray.50">
        <Button colorScheme="primary" size="xs" data-testid="add-btn">
          Configure {flowType}s <GearLightIcon marginLeft={2} />
        </Button>
        <Text size="xs" lineHeight={4} fontWeight="medium">
          {flowType} Systems
        </Text>
        {systems.map((dataFlow) => (
          <div key={dataFlow.fides_key}>{dataFlow.fides_key}</div>
        ))}
      </AccordionPanel>
    </AccordionItem>
  );
};

type DataFlowFormProps = {
  system: System;
};

export const DataFlowForm = ({ system }: DataFlowFormProps) => {
  console.log(system);
  return (
    <Accordion allowToggle>
      <DataFlowAccordionItem systems={system.ingress!} isIngress />
      <DataFlowAccordionItem systems={system.egress!} />
    </Accordion>
  );
};
