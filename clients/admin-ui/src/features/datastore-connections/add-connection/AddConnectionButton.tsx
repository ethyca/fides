import { Button } from "fidesui";
import NextLink from "next/link";
import React from "react";

import { STEPS } from "./constants";

const AddConnectionButton: React.FC = () => (
  <NextLink href={STEPS[1].href} passHref>
    <Button
      bg="primary.800"
      color="white"
      flexShrink={0}
      size="sm"
      variant="solid"
      _hover={{ bg: "primary.400" }}
      _active={{ bg: "primary.500" }}
    >
      Create new connection
    </Button>
  </NextLink>
);

export default AddConnectionButton;
