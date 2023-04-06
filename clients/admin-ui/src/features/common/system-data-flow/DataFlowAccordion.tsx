import { Accordion } from "@fidesui/react";
import React from "react";

import { System } from "~/types/api/models/System";

import { DataFlowAccordionForm } from "./DataFlowAccordionForm";

type DataFlowFormProps = {
  system: System;
};

export const DataFlowAccordion = ({ system }: DataFlowFormProps) => {
  return (
    <Accordion allowToggle>
      <DataFlowAccordionForm dataFlows={system.ingress!} isIngress />
      <DataFlowAccordionForm dataFlows={system.egress!} />
    </Accordion>
  );
};
