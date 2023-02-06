import React, { useMemo } from "react";
import {
  Flex,
  Box,
  Text,
  Link,
  Radio,
  RadioGroup,
  Stack,
  HStack,
} from "@fidesui/react";
import { ExternalLinkIcon } from "@chakra-ui/icons";
import { getConsentContext, resolveConsentValue } from "fides-consent";

import { ConfigConsentOption } from "~/types/config";
import { useAppDispatch, useAppSelector } from "~/app/hooks";
import {
  changeConsent,
  selectFidesKeyToConsent,
} from "~/features/consent/consent.slice";

type ConsentItemProps = {
  option: ConfigConsentOption;
};

const ConsentItemCard = ({ option }: ConsentItemProps) => {
  const { name, description, highlight, url, fidesDataUseKey } = option;

  const defaultValue = useMemo(
    () => resolveConsentValue(option.default, getConsentContext()),
    [option]
  );

  const dispatch = useAppDispatch();
  const fidesKeyToConsent = useAppSelector(selectFidesKeyToConsent);

  const value = fidesKeyToConsent[option.fidesDataUseKey] ?? defaultValue;

  const handleRadioChange = (radioValue: string) => {
    dispatch(changeConsent({ option, value: radioValue === "true" }));
  };

  return (
    <Flex
      flexDirection="row"
      width="720px"
      backgroundColor={highlight ? "gray.100" : undefined}
      justifyContent="center"
      data-testid={`consent-item-card-${fidesDataUseKey}`}
    >
      <Flex mb="24px" mt="24px" mr="35px" ml="35px" width="100%">
        <Box width="100%" pr="60px">
          <Text
            fontSize="lg"
            fontWeight="bold"
            lineHeight="7"
            color="gray.600"
            mb="4px"
          >
            {name}
          </Text>
          <Text
            fontSize="sm"
            fontWeight="medium"
            lineHeight="5"
            color="gray.600"
            mb="2px"
          >
            {description}
          </Text>
          <Link href={url} isExternal>
            <HStack>
              <Text
                fontSize="sm"
                fontWeight="medium"
                lineHeight="5"
                color="complimentary.500"
              >
                {" "}
                Find out more about this consent{" "}
              </Text>
              <ExternalLinkIcon mx="2px" color="complimentary.500" />
            </HStack>
          </Link>
        </Box>
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
      </Flex>
    </Flex>
  );
};

export default ConsentItemCard;
