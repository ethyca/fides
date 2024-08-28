import { Button } from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";

import ErrorLayout from "~/components/ErrorLayout";

const Custom404: NextPage = () => (
  <ErrorLayout
    title="Error: 404"
    description="We're sorry, but this page doesn't exist."
  >
    <Button
      width={320}
      as={NextLink}
      href="/"
      bg="primary.800"
      _hover={{ bg: "primary.400" }}
      _active={{ bg: "primary.500" }}
      colorScheme="primary"
    >
      Return to homepage
    </Button>
  </ErrorLayout>
);

export default Custom404;
