import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Button,
  Flex,
  IconButton,
  Spacer,
  Tag,
  Text,
} from "@fidesui/react";
import { GearLightIcon } from "common/Icon";
import { TrashCanSolidIcon } from "common/Icon/TrashCanSolidIcon";
import QuestionTooltip from "common/QuestionTooltip";
import React from "react";

import { useGetAllSystemsQuery } from "~/features/system";
import { DataFlow } from "~/types/api";
import { System } from "~/types/api/models/System";

type DataFlowItemProps = {
  dataFlow: DataFlow;
};

const DataFlowItem = ({ dataFlow }: DataFlowItemProps) => {
  const { data: system } = useGetAllSystemsQuery(undefined, {
    selectFromResult: ({ data }) => ({
      data: data?.find((s) => s.fides_key === dataFlow.fides_key),
    }),
  });

  return (
    <Flex
      alignItems="center"
      height="40px"
      padding={1}
      borderTop="solid 1px"
      borderTopColor="gray.200"
    >
      <Text fontSize="xs" lineHeight={4} fontWeight="medium">
        {system ? system.name : dataFlow.fides_key}
      </Text>
      <Spacer />
      <IconButton
        size="xs"
        variant="outline"
        aria-label="Remove system"
        icon={<TrashCanSolidIcon />}
      />
    </Flex>
  );
};

type DataFlowAccordionItemProps = {
  isIngress?: boolean;
  systems: DataFlow[];
};

const DataFlowAccordionItem = ({
  systems,
  isIngress,
}: DataFlowAccordionItemProps) => {
  const flowType = isIngress ? "Source" : "Destination";
  const pluralFlowType = `${flowType}s`;

  return (
    <AccordionItem>
      <AccordionButton height="44px" padding={2}>
        <Flex
          alignItems="center"
          justifyContent="start"
          flex={1}
          textAlign="left"
        >
          <Text fontSize="sm" lineHeight={5} fontWeight="semibold" mr={4}>
            {pluralFlowType}
          </Text>
          <QuestionTooltip label="helpful tip" />

          <Tag
            ml={2}
            backgroundColor="primary.400"
            borderRadius="6px"
            color="white"
          >
            {systems.length}
          </Tag>
          <Spacer />
          <AccordionIcon />
        </Flex>
      </AccordionButton>
      <AccordionPanel backgroundColor="gray.50" padding={6}>
        <Button
          colorScheme="primary"
          size="xs"
          data-testid="add-btn"
          marginBottom={4}
        >
          Configure {pluralFlowType} <GearLightIcon marginLeft={2} />
        </Button>
        <Text
          fontSize="xs"
          lineHeight={4}
          fontWeight="medium"
          marginBottom={3}
          casing="uppercase"
        >
          {flowType} Systems
        </Text>
        {systems.map((dataFlow) => (
          <DataFlowItem key={dataFlow.fides_key} dataFlow={dataFlow} />
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
