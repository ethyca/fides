import { Box, Button, Center, Stack, Text } from "@fidesui/react";

import { ADD_SYSTEMS_ROUTE } from "../common/nav/v2/routes";

const GetStarted = () => (
  <Center flex={1} data-testid="get-started-modal" backgroundColor="gray.100">
    <Box
      backgroundColor="white"
      p={10}
      borderRadius="6px"
      boxShadow="0px 1px 3px rgba(0, 0, 0, 0.1), 0px 1px 2px rgba(0, 0, 0, 0.06)"
      maxWidth={{ base: "80%", lg: "60%", xl: "50%" }}
      maxHeight="90%"
      textAlign="center"
    >
      <Stack spacing={4}>
        <Text color="gray.700" fontWeight="600">
          Privacy engineering can seem like an endlessly complex confluence of
          legal and data engineering terminology&mdash;fear not&mdash;Fides is
          here to simplify this.
        </Text>
        <Text>
          Start by scanning your infrastructure. The scanner will connect to
          your infrastructure to automatically scan and create a list of all
          systems available and then classify each system containing PII.
        </Text>
        <Text>Let&apos;s get started!</Text>
        <Box>
          <Button
            as="a"
            href={ADD_SYSTEMS_ROUTE}
            width="fit-content"
            colorScheme="primary"
            data-testid="add-systems-btn"
          >
            Add Systems
          </Button>
        </Box>
      </Stack>
    </Box>
  </Center>
);

export default GetStarted;
