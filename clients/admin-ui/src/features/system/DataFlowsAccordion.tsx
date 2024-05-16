import { Accordion, Stack, Text } from "fidesui";

import { ClassifySystem, DataFlow, System } from "~/types/api";

import DataFlowsAccordionItem from "./DataFlowsAccordionItem";

export interface IngressEgress {
  ingress: DataFlow[];
  egress: DataFlow[];
}

const DataFlowsAccordion = ({
  system,
  classificationInstance,
}: {
  system: System;
  classificationInstance?: ClassifySystem;
}) => {
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
        <DataFlowsAccordionItem
          classifyDataFlows={classificationInstance?.ingress}
          type="ingress"
        />
        <DataFlowsAccordionItem
          classifyDataFlows={classificationInstance?.egress}
          type="egress"
        />
      </Accordion>
    </Stack>
  );
};

export default DataFlowsAccordion;
