import { Box, Heading, Stack, Text } from "fidesui";

interface ErrorLayoutProps {
  title: string;
  description: string;
  children?: React.ReactNode;
}

const ErrorLayout = ({ title, description, children }: ErrorLayoutProps) => (
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
              {title}
            </Heading>
            <Text fontWeight="semibold">{description}</Text>
            {children}
          </Stack>
        </Stack>
      </Box>
    </Stack>
  </Box>
);

export default ErrorLayout;
