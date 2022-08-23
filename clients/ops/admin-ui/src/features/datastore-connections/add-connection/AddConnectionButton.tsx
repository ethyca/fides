import { Button } from "@fidesui/react";
import NextLink from "next/link";
import React from "react";

import { DATASTORE_CONNECTION_ROUTE } from "../../../constants";

const AddConnectionButton: React.FC = () => (
  <NextLink href={`${DATASTORE_CONNECTION_ROUTE}/new?step=1`} passHref>
    <Button
      bg="primary.800"
      color="white"
      flexShrink={0}
      size="sm"
      variant="solid"
    >
      Create New Connection
    </Button>
  </NextLink>
);

export default AddConnectionButton;
