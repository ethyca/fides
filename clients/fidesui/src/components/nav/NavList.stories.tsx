import { Box, Heading, Stack } from "@fidesui/react";
import React from "react";

import { SecondaryLink } from "../links/SecondaryLink";
import { NavList } from "./NavList";

export default {
  title: "Components/NavList",
  component: NavList,
};

export const NavListStory = () => (
  <Stack>
    <Heading size="md">Nav List</Heading>
    <Box maxW="50%" bg="white" borderRadius="md">
      <NavList>
        <SecondaryLink href="https://example.com" isActive>
          Nav Item 1
        </SecondaryLink>
        <SecondaryLink href="https://example.com">Nav Item 2</SecondaryLink>
        <SecondaryLink href="https://example.com">Nav Item 3</SecondaryLink>
        <SecondaryLink href="https://example.com">Nav Item 4</SecondaryLink>
        <SecondaryLink href="https://example.com">Nav Item 5</SecondaryLink>
        <SecondaryLink href="https://example.com">Nav Item 6</SecondaryLink>
        <SecondaryLink href="https://example.com">Ethyca</SecondaryLink>
      </NavList>
    </Box>
  </Stack>
);
