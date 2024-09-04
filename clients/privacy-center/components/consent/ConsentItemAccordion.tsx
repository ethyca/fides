import { GpcStatus } from "fides-js";
import {
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  Flex,
  Text,
} from "fidesui";
import React from "react";

import { GpcBadge, GpcInfo } from "~/features/consent/GpcMessages";

import Toggle from "./Toggle";

export type ConsentItemAccordionProps = {
  id: string;
  title: string;
  description: string;
  value: boolean;
  gpcStatus: GpcStatus;
  onChange: (value: boolean) => void;
  disabled?: boolean;
};

const ConsentItemAccordion = ({
  id,
  title,
  description,
  value,
  gpcStatus,
  onChange,
  disabled,
}: ConsentItemAccordionProps) => (
  <AccordionItem data-testid={`consent-item-${id}`} width="full">
    <AccordionButton pl={2}>
      <Flex justifyContent="space-between" alignItems="center" width="full">
        <Flex alignItems="center">
          <AccordionIcon fontSize={26} />
          <Text
            fontSize="lg"
            fontWeight="medium"
            color="gray.600"
            ml={1}
            mb="4px"
          >
            {title}
          </Text>
        </Flex>
        <Flex alignItems="center">
          <GpcBadge status={gpcStatus} />
          <Flex ml={2} onClick={(e) => e.stopPropagation()}>
            <Toggle
              label={title}
              name={id}
              id={id}
              disabled={disabled}
              checked={value}
              onChange={() => onChange(!value)}
            />
          </Flex>
        </Flex>
      </Flex>
    </AccordionButton>
    <AccordionPanel>
      <Box pt={2}>
        <GpcInfo status={gpcStatus} />
        <Text
          fontSize="sm"
          fontWeight="medium"
          color="gray.600"
          mb="2px"
          pr={8}
        >
          {description}
        </Text>
      </Box>
    </AccordionPanel>
  </AccordionItem>
);

export default ConsentItemAccordion;
