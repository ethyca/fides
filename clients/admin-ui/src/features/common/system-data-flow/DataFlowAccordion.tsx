import { Accordion } from "@fidesui/react";
import React from "react";

import { System } from "~/types/api/models/System";

import { DataFlowAccordionForm } from "./DataFlowAccordionForm";

type DataFlowFormProps = {
  system: System;
  isSystemTab?: boolean;
};

export const DataFlowAccordion = ({
  system,
  isSystemTab,
}: DataFlowFormProps) => (
  <Accordion allowToggle data-testid="data-flow-accordion">
    <DataFlowAccordionForm
      system={system}
      isIngress
      isSystemTab={isSystemTab}
    />
    <DataFlowAccordionForm system={system} isSystemTab={isSystemTab} />
  </Accordion>
);
