import React, { useState, useEffect } from "react";
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
import { ConsentItem } from "../types";

type SetConsentValueProp = {
  setConsentValue: (x: boolean) => void;
};

type ConsentItemProps = ConsentItem & SetConsentValueProp;

const ConsentItemCard: React.FC<ConsentItemProps> = ({
  name,
  description,
  highlight,
  defaultValue,
  consentValue,
  url,
  setConsentValue,
}) => {
  const [value, setValue] = useState("false");
  const backgroundColor = highlight ? "gray.100" : "";
  useEffect(() => {
    if (consentValue !== undefined) {
      setValue(consentValue ? "true" : "false");
    } else {
      setValue(defaultValue ? "true" : "false");
      setConsentValue(defaultValue);
    }
  }, [consentValue, defaultValue, setValue, setConsentValue]);

  return (
    <Flex
      flexDirection="row"
      width="720px"
      backgroundColor={backgroundColor}
      justifyContent="center"
    >
      <Flex mb="24px" mt="24px" mr="35px" ml="35px">
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
          onChange={(e) => {
            setValue(e);
            setConsentValue(e === "true");
          }}
          value={value}
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
