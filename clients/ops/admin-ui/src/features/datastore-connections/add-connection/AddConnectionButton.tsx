import { Button, Tooltip } from "@fidesui/react";
import NextLink from "next/link";
import React from "react";
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { Flags } from "react-feature-flags";

import { STEPS } from "./constants";

const AddConnectionButton: React.FC = () => (
  <Flags
    authorizedFlags={["createNewConnection"]}
    renderOn={() => (
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
          Create New Connection
        </Button>
      </NextLink>
    )}
    renderOff={() => (
      <Tooltip
        aria-label="This feature is not available"
        hasArrow
        label="This feature is not available"
        placement="auto-start"
        openDelay={500}
        shouldWrapChildren
      >
        <Button
          bg="primary.100"
          color="white"
          flexShrink={0}
          pointerEvents="none"
          size="sm"
          variant="solid"
        >
          Create New Connection
        </Button>
      </Tooltip>
    )}
  />
);

export default AddConnectionButton;
