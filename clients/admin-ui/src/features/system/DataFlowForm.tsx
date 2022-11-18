import { Accordion, Stack, Text } from "@fidesui/react";
import { Form, Formik } from "formik";

import { ClassifySystem, DataFlow, System } from "~/types/api";

import DataFlowsAccordionItem from "./DataFlowsAccordionItem";

export const FORM_ID = "data-flow-form";
export interface IngressEgress {
  ingress: DataFlow[];
  egress: DataFlow[];
}

const DataFlowForm = ({
  system,
  onSave,
  classificationInstance,
}: {
  system: System;
  onSave: (flows: IngressEgress) => void;
  classificationInstance?: ClassifySystem;
}) => {
  const hasNoDataFlows =
    (system.ingress == null || system.ingress.length === 0) &&
    (system.egress == null || system.egress.length === 0);

  if (hasNoDataFlows) {
    return <Text>No data flows found on this system.</Text>;
  }

  const initialValues: IngressEgress = {
    egress: system.egress ?? [],
    ingress: system.ingress ?? [],
  };

  return (
    <Formik initialValues={initialValues} onSubmit={onSave}>
      <Form id={FORM_ID}>
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
      </Form>
    </Formik>
  );
};

export default DataFlowForm;
