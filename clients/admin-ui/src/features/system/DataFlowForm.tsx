import { Accordion, Box, Button, Stack, Text } from "@fidesui/react";
import { Form, Formik } from "formik";

import { ClassifySystem, DataFlow, System } from "~/types/api";

import DataFlowsAccordionItem from "./DataFlowsAccordionItem";

export interface IngressEgress {
  ingress: DataFlow[];
  egress: DataFlow[];
}

const DataFlowForm = ({
  onClose,
  system,
  onSave,
  classificationInstance,
}: {
  system: System;
  onSave: (flows: IngressEgress) => void;
  onClose: () => void;
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
      <Form>
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
          <Box>
            <Button onClick={onClose} mr={2} size="sm" variant="outline">
              Cancel
            </Button>
            <Button
              type="submit"
              colorScheme="primary"
              size="sm"
              data-testid="save-btn"
            >
              Save
            </Button>
          </Box>
        </Stack>
      </Form>
    </Formik>
  );
};

export default DataFlowForm;
