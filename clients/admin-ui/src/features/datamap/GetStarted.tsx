import {
  Button,
  ChakraBox as Box,
  ChakraCenter as Center,
  ChakraStack as Stack,
  ChakraText as Text,
} from "fidesui";

import { ADD_SYSTEMS_ROUTE } from "../common/nav/routes";

const GetStarted = () => {
  return (
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
            Start by adding systems. You can connect to AWS or Okta to discover
            services automatically, add vendors in bulk with Compass, or enter
            systems manually—then classify systems that process personal data.
          </Text>
          <Text>Let&apos;s get started!</Text>
          <Box>
            <Button
              href={ADD_SYSTEMS_ROUTE}
              role="link"
              type="primary"
              className="w-fit"
              data-testid="add-systems-btn"
            >
              Add Systems
            </Button>
          </Box>
        </Stack>
      </Box>
    </Center>
  );
};

export default GetStarted;
