import { Box, Button, Stack, Text } from "@fidesui/react";

const ConfigurationNotificationBanner = () => (
  <Box
    bg="gray.50"
    border="1px solid"
    borderColor="blue.400"
    borderRadius="md"
    justifyContent="space-between"
    p={5}
    mb={5}
    mt={5}
  >
    <Box>
      <Stack
        direction={{ base: "column", sm: "row" }}
        justifyContent="space-between"
      >
        <Text fontWeight="semibold">
          {/* ICON */}
          Configure your storage and messaging provider
        </Text>
        <Button
          size="sm"
          variant="outline"
          // onClick route to cofiguration page
        >
          Configure
        </Button>
      </Stack>

      <Text color="muted">
        Before Fides can process your privacy requests we need two simple steps
        to configure your storage and email client.{" "}
      </Text>
    </Box>
  </Box>
);
export default ConfigurationNotificationBanner;
