"use client";

import {
  Button,
  ChakraBox as Box,
  ChakraFlex as Flex,
  ChakraHeading as Heading,
  ChakraImage as Image,
  ChakraLink as Link,
  ChakraStack as Stack,
  ChakraText as Text,
} from "fidesui";
import { useState } from "react";
import { FallbackProps } from "react-error-boundary";

import { useAppSelector } from "~/app/hooks";

export const DEFAULT_ERROR_MESSAGE =
  "The Privacy Center is currently unavailable. Please try again later.";

const Error = ({ resetErrorBoundary }: FallbackProps) => {
  const config = useAppSelector((state) => state.config.config);
  const message = config?.error_message?.trim()
    ? config.error_message
    : DEFAULT_ERROR_MESSAGE;
  const logoPath = config?.logo_path;
  const logoUrl = config?.logo_url;
  const [logoFailed, setLogoFailed] = useState(false);
  const showLogo = Boolean(logoPath) && !logoFailed;

  const logoImage = (
    <Image
      src={logoPath || undefined}
      alt="Logo"
      margin="8px"
      height="68px"
      data-testid="logo"
      onError={() => setLogoFailed(true)}
    />
  );

  return (
    <Box
      as="main"
      bg="gray.50"
      minH="100vh"
      display="flex"
      flexDirection="column"
    >
      {showLogo ? (
        <Flex
          bg="gray.75"
          minHeight={14}
          p={1}
          width="100%"
          justifyContent="center"
          alignItems="center"
        >
          {logoUrl ? <Link href={logoUrl}>{logoImage}</Link> : logoImage}
        </Flex>
      ) : null}
      <Stack flex="1" align="center" justify="center" spacing={6} py={8} px={4}>
        <Box
          bg="white"
          py={8}
          px={[4, 4, 35]}
          width={["100%", "100%", 640]}
          borderRadius={4}
          boxShadow="base"
        >
          <Stack align="center" justify="center" spacing={3}>
            <Heading
              fontSize="3xl"
              lineHeight="1"
              colorScheme="primary"
              color="gray.700"
            >
              Error
            </Heading>
            <Text fontWeight="semibold" textAlign="center">
              {message}
            </Text>
            <Button variant="text" onClick={resetErrorBoundary}>
              Try again
            </Button>
          </Stack>
        </Box>
      </Stack>
    </Box>
  );
};

export default Error;
