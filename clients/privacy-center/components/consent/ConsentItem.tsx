import React from "react";
import {
  Box,
  Flex,
  HStack,
  Link,
  Radio,
  RadioGroup,
  Spacer,
  Stack,
  Text,
  ExternalLinkIcon,
} from "@fidesui/react";

import { GpcStatus } from "~/features/consent/types";
import { GpcBadge, GpcInfo } from "~/features/consent/GpcMessages";

export type ConsentItemProps = {
  id: string;
  name: string;
  description: string;
  highlight?: boolean;
  url?: string;
  value: boolean;
  gpcStatus: GpcStatus;
  onChange: (value: boolean) => void;
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
}: ConsentItemProps) => {
  const handleRadioChange = (radioValue: string) => {
    onChange(radioValue === "true");
  };

  return (
    <Box
      backgroundColor={highlight ? "gray.100" : undefined}
      borderRadius="md"
      data-testid={`consent-item-${id}`}
      paddingX={12}
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

        <HStack spacing={10}>
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
            <RadioGroup
              value={value ? "true" : "false"}
              onChange={handleRadioChange}
            >
              <Stack direction="row">
                <Radio value="true" colorScheme="whatsapp">
                  Yes
                </Radio>
                <Radio value="false" colorScheme="whatsapp">
                  No
                </Radio>
              </Stack>
            </RadioGroup>
          </Box>
        </HStack>
      </Stack>
    </Box>
  );
};

export default ConsentItem;
