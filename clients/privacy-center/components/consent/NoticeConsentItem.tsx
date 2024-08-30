import { GpcStatus } from "fides-js";
import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  Flex,
  HStack,
  Spacer,
  Stack,
  Text,
} from "fidesui";
import React from "react";

import { GpcBadge, GpcInfo } from "~/features/consent/GpcMessages";

import Toggle from "./Toggle";

export type NoticeConsentItemProps = {
  id: string;
  title: string;
  description: string;
  value: boolean;
  gpcStatus: GpcStatus;
  onChange: (value: boolean) => void;
  disabled?: boolean;
};

const NoticeConsentItem = ({
  id,
  title,
  description,
  value,
  gpcStatus,
  onChange,
  disabled,
}: NoticeConsentItemProps) => (
  <Box
    borderRadius="md"
    data-testid={`consent-item-${id}`}
    paddingY={3}
    width="full"
    lineHeight={5}
  >
    <Accordion allowToggle>
      <AccordionItem>
        <AccordionButton pl={2}>
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
          <Spacer />
          <GpcBadge status={gpcStatus} />
        </AccordionButton>
        <AccordionPanel>
          <Text fontSize="sm" fontWeight="medium" color="gray.600" mb="2px">
            {description}
          </Text>
        </AccordionPanel>
      </AccordionItem>
    </Accordion>
    <Stack>
      <Flex direction="row">
        <Text fontSize="lg" fontWeight="bold" color="gray.600" mb="4px">
          {title}
        </Text>
        <Spacer />
        <GpcBadge status={gpcStatus} />
      </Flex>

      <GpcInfo status={gpcStatus} />

      <HStack spacing={10} justifyContent="space-between">
        <Stack>
          <Text fontSize="sm" fontWeight="medium" color="gray.600" mb="2px">
            {description}
          </Text>
        </Stack>

        <Box>
          <Toggle
            label={title}
            name={id}
            id={id}
            disabled={disabled}
            checked={value}
            onChange={() => onChange(!value)}
          />
        </Box>
      </HStack>
    </Stack>
  </Box>
);

export default NoticeConsentItem;
