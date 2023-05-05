import { Stack, Heading, Box, Text, Button, Code } from "@fidesui/react";

import { FallbackProps } from "react-error-boundary";

const Error: React.FC<FallbackProps> = ({ error, resetErrorBoundary }) => (
    <div>
      <main>
        <Stack minH="100vh" align="center" justify="center" spacing={6}>
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
              <Stack width="100%" align="center" justify="center" spacing={3}>
                <Heading
                  fontSize="3xl"
                  lineHeight="1"
                  colorScheme="primary"
                  color="gray.700"
                >
                  Error
                </Heading>
                <Text fontWeight="semibold">
                  We’re sorry, but an unexpected error occurred.
                </Text>
                {error?.message ?
                  <Code height={200} width="80%" overflowY="auto" padding={4} fontWeight="semibold">
                    {error.message}
                  </Code>
                  : null}
                <Button
                  width={320}
                  as="a"
                  bg="primary.800"
                  _hover={{ bg: "primary.400" }}
                  _active={{ bg: "primary.500" }}
                  colorScheme="primary"
                  onClick={resetErrorBoundary}
                >
                  Try again
                </Button>
              </Stack>
            </Stack>
          </Box>
        </Stack>
      </main>
    </div>
  );

export default Error;
