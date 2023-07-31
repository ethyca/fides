import { Stack, Box, Heading } from "@fidesui/react";

const SystemFormInputGroup = ({
  heading,
  children,
}: {
  heading: string;
  children?: React.ReactNode;
}) => (
  <Stack spacing={4}>
    <Box maxWidth="720px" border="1px" borderColor="gray.200" borderRadius={6}>
      <Box
        backgroundColor="gray.50"
        px={6}
        py={4}
        borderBottom="1px"
        borderColor="gray.200"
        borderTopRadius={6}
      >
        <Heading as="h3" size="xs">
          {heading}
        </Heading>
      </Box>

      <Stack spacing={4} px={6} py={6}>
        {children}
      </Stack>
    </Box>
  </Stack>
);

export default SystemFormInputGroup;
