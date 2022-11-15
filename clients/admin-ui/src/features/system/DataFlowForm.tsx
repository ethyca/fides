import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  Heading,
  Stack,
  Text,
} from "@fidesui/react";
import { ReactNode } from "react";

import { ClassifySystem, DataFlow, System } from "~/types/api";

const AccordionItemContents = ({
  headingLevel,
  title,
  children,
}: {
  headingLevel: "h2" | "h3";
  title: string;
  children: ReactNode;
}) => (
  <>
    <Heading as={headingLevel}>
      <AccordionButton
        _expanded={{ color: "complimentary.500" }}
        _hover={{ bg: "gray.50" }}
        pl={0}
      >
        <Box flex="1" textAlign="left">
          {title}
        </Box>
        <AccordionIcon />
      </AccordionButton>
    </Heading>

    <AccordionPanel p={0}>{children}</AccordionPanel>
  </>
);

const DataFlows = ({
  dataFlows,
  type,
}: {
  dataFlows?: DataFlow[];
  type: "ingress" | "egress";
}) => {
  if (dataFlows == null || dataFlows.length === 0) {
    return <Text p={4}>No {type}es found.</Text>;
  }
  return (
    <AccordionItem p={0}>
      <AccordionItemContents
        headingLevel="h2"
        title={`Connected ${
          type[0].toLocaleUpperCase() + type.slice(1)
        } Systems`}
      >
        {dataFlows.map((flow) => (
          <AccordionItem key={flow.fides_key} pl={4}>
            <AccordionItemContents headingLevel="h3" title={flow.fides_key}>
              {flow.data_categories?.join(" ")}
            </AccordionItemContents>
          </AccordionItem>
        ))}
      </AccordionItemContents>
    </AccordionItem>
  );
};

const DataFlowForm = ({
  system,
  classificationInstance,
}: {
  system: System;
  classificationInstance?: ClassifySystem;
}) => {
  console.log({ system });
  const hasNoDataFlows =
    (system.ingress == null || system.ingress.length === 0) &&
    (system.egress == null || system.egress.length === 0);

  if (hasNoDataFlows) {
    return <Text>No data flows found on this system.</Text>;
  }

  return (
    <Stack>
      <Text fontWeight="semibold">{system.name}</Text>
      <Accordion allowMultiple pl={2}>
        <DataFlows dataFlows={system.ingress} type="ingress" />
        <DataFlows dataFlows={system.egress} type="egress" />
      </Accordion>
    </Stack>
  );
};

export default DataFlowForm;
