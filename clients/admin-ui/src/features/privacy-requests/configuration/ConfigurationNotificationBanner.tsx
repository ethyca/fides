import { AntButton as Button, Box, Stack, Text } from "fidesui";
import { useRouter } from "next/router";

import { MESSAGING_CONFIGURATION_ROUTE } from "~/features/common/nav/v2/routes";

const ConfigurationNotificationBanner = () => {
  const router = useRouter();

  const handleClick = () => {
    router.push(MESSAGING_CONFIGURATION_ROUTE);
  };

  return (
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
            Configure your storage and messaging provider
          </Text>
          <Button onClick={handleClick}>Configure</Button>
        </Stack>

        <Text>
          Before Fides can process your privacy requests we need two simple
          steps to configure your storage and email client.{" "}
        </Text>
      </Box>
    </Box>
  );
};
export default ConfigurationNotificationBanner;
