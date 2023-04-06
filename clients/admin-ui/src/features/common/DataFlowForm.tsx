import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Flex,
  Tag,
  Text,
  Button,
  Spacer,
  Divider,
  Box,
} from "@fidesui/react";
import { System } from "~/types/api/models/System";
import { DataFlow } from "~/types/api";
import React from "react";
import { GearLightIcon } from "common/Icon";
import QuestionTooltip from "common/QuestionTooltip";
import { useGetAllSystemsQuery } from "~/features/system";

type DataFlowItemProps = {
  dataFlow: DataFlow;
};

const DataFlowItem = ({ dataFlow }: DataFlowItemProps) => {
  const { data: system } = useGetAllSystemsQuery(undefined, {
    selectFromResult: ({ data }) => ({
      data: data?.find((s) => s.fides_key === dataFlow.fides_key),
    }),
  });

  return <Box>{system ? system.name : dataFlow.fides_key}</Box>;
};

type DataFlowAccordionItemProps = {
  isIngress?: boolean;
  systems: DataFlow[];
};

const DataFlowAccordionItem = ({
  systems,
  isIngress,
}: DataFlowAccordionItemProps) => {
  const flowType = isIngress ? "Sources" : "Destinations";

  return (
    <AccordionItem>
      <AccordionButton height="44px">
        <Flex
          alignItems="center"
          justifyContent="start"
          flex={1}
          textAlign="left"
        >
          <Text size="sm" lineHeight={5} fontWeight="semibold" mr={4}>
            {flowType}
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
          Configure {flowType} <GearLightIcon marginLeft={2} />
        </Button>
        <Text size="xs" lineHeight={4} fontWeight="medium" marginBottom={3}>
          {flowType} Systems
        </Text>
        <Divider />
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
