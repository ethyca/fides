import { Flex } from "fidesui";
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
  <Flex vertical data-testid="data-flow-accordion">
    <DataFlowAccordionForm
      system={system}
      isIngress
      isSystemTab={isSystemTab}
    />
    <DataFlowAccordionForm system={system} isSystemTab={isSystemTab} />
  </Flex>
);
