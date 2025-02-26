import { Accordion } from "fidesui";
import React from "react";

import { System } from "~/types/api";

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
