import { Heading, VStack } from "@fidesui/react";
import React from "react";

import { SecondaryLink } from "./SecondaryLink";

export default {
  title: "Components/SecondaryLink",
  component: SecondaryLink,
};

export const SecondaryLinkStory = () => (
  <VStack align="left">
    <Heading size="md">Secondary Link</Heading>
    <VStack
      spacing="15px"
      align="left"
      w="300px"
      p="15px"
      bg="white"
      borderRadius="md"
    >
      <SecondaryLink>No href</SecondaryLink>

      <SecondaryLink href="/">Current page href</SecondaryLink>

      <SecondaryLink href="https://example.com" isExternal>
        External page href
      </SecondaryLink>

      <SecondaryLink href="/" isActive>
        Set isActive
      </SecondaryLink>

      <SecondaryLink href="/" isDisabled>
        Set isDisabled
      </SecondaryLink>
    </VStack>
  </VStack>
);
