import { Box, Button, Heading, Stack, Text } from '@fidesui/react';
import Head from 'next/head';
import Image from 'next/image';
import NextLink from 'next/link';

const Custom404 = () => (
  <div>
    <Head>
      <title>FidesUI App</title>
      <meta name="description" content="Generated from FidesUI template" />
      <link rel="icon" href="/favicon.ico" />
    </Head>

    <main>
      <Stack minH="100vh" align="center" justify="center" spacing={6}>
        <Box
          bg="white"
          py={16}
          px={[0, 0, 35]}
          width={['100%', '100%', 640]}
          borderRadius={4}
          position={['absolute', 'absolute', 'inherit']}
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
                  _hover={{ bg: 'primary.400' }}
                  _active={{ bg: 'primary.500' }}
                  colorScheme="primary"
                >
                  Return to homepage
                </Button>
              </NextLink>
            </Stack>
            <Box display={[null, null, 'none']}>
              <Image
                src="/logo.svg"
                alt="FidesUI logo"
                width="124px"
                height="38px"
              />
            </Box>
          </Stack>
        </Box>
        <Box display={['none', 'none', 'inherit']}>
          <Image
            src="/logo.svg"
            alt="FidesUI logo"
            width="124px"
            height="38px"
          />
        </Box>
      </Stack>
    </main>
  </div>
);

export default Custom404;
