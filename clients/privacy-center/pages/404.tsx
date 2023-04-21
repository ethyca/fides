import NextLink from "next/link";
import type { NextPage } from "next";
import { Stack, Heading, Box, Text, Button, Link, Image } from "@fidesui/react";

import { useConfig } from "~/features/common/config.slice";

const Custom404: NextPage = () => {
  const config = useConfig();
  return (
    <div>
      <main>
        <Stack minH="100vh" align="center" justify="center" spacing={6}>
          <Box
            bg="white"
            py={16}
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
                  fontSize="7xl"
                  lineHeight="1"
                  colorScheme="primary"
                  color="gray.700"
                >
                  Error: 404
                </Heading>
                <Text fontWeight="semibold">
                  We’re sorry but this page doesn’t exist
                </Text>
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
              </Stack>
              <Box display={[null, null, "none"]}>
                <Image
                  src={config.logo_path}
                  alt="Logo"
                  maxWidth="200px"
                  maxHeight="100px"
                />
              </Box>
            </Stack>
          </Box>
          <Box display={["none", "none", "inherit"]}>
            <NextLink href="/" passHref>
              {/* eslint-disable-next-line jsx-a11y/anchor-is-valid */}
              <Link>
                <Image
                  src={config.logo_path}
                  alt="Logo"
                  maxWidth="200px"
                  maxHeight="100px"
                />
              </Link>
            </NextLink>
          </Box>
        </Stack>
      </main>
    </div>
  );
}

export default Custom404;
