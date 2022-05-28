import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Stack,
  Text,
  Tooltip,
} from "@fidesui/react";

const OrganizationInfoForm = (handleChangeStep: any) => {
  return (
    <Box borderWidth="1px" borderRadius="lg">
      <Heading as="h3" size="lg">
        Tell us about your business
      </Heading>
      <Text>
        Provide your organization information. This information is used to
        configure your organization in Fidesctl for{" "}
        <Text display="inline" color="complimentary.500">
          data map
        </Text>{" "}
        reporting purposes.
      </Text>
      <Stack>
        <FormControl>
          <FormLabel>Organization name</FormLabel>
          <Stack direction={"row"}>
            <Input
              type="text"
              // value={}
              // onChange={handleInputChange}
            />
            <Tooltip label="The legal name of your organization" fontSize="md">
              {/* <Icon /> */}
              Hi
            </Tooltip>
          </Stack>
          <FormLabel>Description</FormLabel>
          <Stack direction={"row"}>
            <Input
              type="text"
              // value={}
              // onChange={handleInputChange}
            />
            <Tooltip
              label="An explanation of the type of organization and primary activity. 
                  For example “Acme Inc. is an e-commerce company that sells scarves.”"
              fontSize="md"
            >
              {/* <Icon /> */}
              Hello
            </Tooltip>
          </Stack>
        </FormControl>
      </Stack>
      <Button
        bg="primary.800"
        _hover={{ bg: "primary.400" }}
        _active={{ bg: "primary.500" }}
        colorScheme="primary"
        onClick={handleChangeStep}
      >
        Save and Continue
      </Button>
    </Box>
  );
};
export default OrganizationInfoForm;
