import { GpcStatus } from "fides-js";
import {
  Box,
  ExternalLinkIcon,
  Flex,
  HStack,
  Link,
  Spacer,
  Stack,
  Text,
} from "fidesui";
import React from "react";

import { GpcBadge, GpcInfo } from "~/features/consent/GpcMessages";

import Toggle from "./Toggle";

export type ConsentItemProps = {
  id: string;
  name: string;
  description: string;
  highlight?: boolean | null;
  url?: string;
  value: boolean;
  gpcStatus: GpcStatus;
  onChange: (value: boolean) => void;
  disabled?: boolean;
};

const ConsentItem = ({
  id,
  name,
  description,
  highlight,
  url,
  value,
  gpcStatus,
  onChange,
  disabled,
}: ConsentItemProps) => (
  <Box
    backgroundColor={highlight ? "gray.100" : undefined}
    borderRadius="md"
    data-testid={`consent-item-${id}`}
    paddingY={3}
    width="full"
    lineHeight={5}
  >
    <Stack>
      <Flex direction="row">
        <Text fontSize="lg" fontWeight="bold" color="gray.600" mb="4px">
          {name}
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
          {url ? (
            <Link href={url} isExternal>
              <HStack>
                <Text
                  fontSize="sm"
                  fontWeight="medium"
                  color="complimentary.500"
                >
                  Find out more about this consent
                </Text>
                <ExternalLinkIcon mx="2px" color="complimentary.500" />
              </HStack>
            </Link>
          ) : null}
        </Stack>

        <Box>
          <Toggle
            label={name}
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

export default ConsentItem;
