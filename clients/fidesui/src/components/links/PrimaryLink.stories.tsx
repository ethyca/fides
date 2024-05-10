import { Heading, VStack } from "@fidesui/react";
import React from "react";

import { PrimaryLink } from "./PrimaryLink";

export default {
  title: "Components/PrimaryLink",
  component: PrimaryLink,
};

export const PrimaryLinkStory = () => (
  <VStack align="left">
    <Heading size="md">Primary Link</Heading>
    <VStack
      spacing="15px"
      align="left"
      w="300px"
      p="15px"
      bg="white"
      borderRadius="md"
    >
      <PrimaryLink>No href</PrimaryLink>

      <PrimaryLink href="/">Current page href</PrimaryLink>

      <PrimaryLink href="https://example.com" isExternal>
        External page href
      </PrimaryLink>

      <PrimaryLink href="/" isActive>
        Set isActive
      </PrimaryLink>

      <PrimaryLink href="/" isDisabled>
        Set isDisabled
      </PrimaryLink>
    </VStack>
  </VStack>
);
