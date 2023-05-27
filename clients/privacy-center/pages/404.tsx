import { Button } from "@fidesui/react";
import type { NextPage } from "next";
import NextLink from "next/link";
import ErrorLayout from "~/components/ErrorLayout";

const Custom404: NextPage = () => (
  <ErrorLayout
    title="Error: 404"
    description="We're sorry, but this page doesn't exist."
  >
    <NextLink href="/" passHref>
      <Button
        width={320}
        as="a"
        bg="primary.800"
        _hover={{ bg: "primary.400" }}
        _active={{ bg: "primary.500" }}
        colorScheme="primary"
      >
        Return to homepage
      </Button>
    </NextLink>
  </ErrorLayout>
);

export default Custom404;
