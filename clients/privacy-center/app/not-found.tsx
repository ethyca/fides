"use client";

import { Box, Button, Heading, Stack, Text } from "fidesui";
import { NextPage } from "next";
import NextLink from "next/link";

const Custom404: NextPage = () => (
  <Box as="main" position="absolute" top={0} right={0} bottom={0} left={0}>
    <Stack
      bg="gray.50"
      minH="100vh"
      align="center"
      justify="center"
      spacing={6}
    >
      <Box
        bg="white"
        py={8}
        px={[0, 0, 35]}
        width={["100%", "100%", 640]}
        borderRadius={4}
        position={["absolute", "absolute", "inherit"]}
        top={0}
        bottom={0}
        left={0}
        right={0}
        boxShadow="base"
      >
        <Stack align="center" spacing={9}>
          <Stack align="center" justify="center" spacing={3}>
            <Heading
              fontSize="3xl"
              lineHeight="1"
              colorScheme="primary"
              color="gray.700"
            >
              Error: 404
            </Heading>
            <Text fontWeight="semibold">
              We&apos;re sorry, but this page doesn&apos;t exist.
            </Text>
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
          </Stack>
        </Stack>
      </Box>
    </Stack>
  </Box>
);

export default Custom404;
