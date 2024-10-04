import Head from "common/Head";
import Image from "common/Image";
import { AntButton, Box, Heading, Stack, Text } from "fidesui";
import { useRouter } from "next/router";

import { INDEX_ROUTE } from "../constants";

const Custom404 = () => {
  const router = useRouter();
  return (
    <div>
      <Head />

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
                <AntButton
                  type="primary"
                  onClick={() => router.push(INDEX_ROUTE)}
                  className="w-80"
                >
                  Return to homepage
                </AntButton>
              </Stack>
              <Box display={[null, null, "none"]}>
                <Image
                  src="/logo.svg"
                  alt="FidesUI logo"
                  width={124}
                  height={38}
                />
              </Box>
            </Stack>
          </Box>
          <Box display={["none", "none", "inherit"]}>
            <Image src="/logo.svg" alt="FidesUI logo" width={124} height={38} />
          </Box>
        </Stack>
      </main>
    </div>
  );
};

export default Custom404;
