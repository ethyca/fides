import {
  Button,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Stack,
  Text,
  Tooltip,
} from "@fidesui/react";
import { QuestionIcon } from "~/features/common/Icon";

const OrganizationInfoForm = (handleChangeStep: any) => {
  return (
    <Stack spacing="24px" w="80%">
      <Heading as="h3" size="lg">
        Tell us about your business
      </Heading>
      <div>
        Provide your organization information. This information is used to
        configure your organization in Fidesctl for{" "}
        <Text display="inline" color="complimentary.500">
          data map
        </Text>{" "}
        reporting purposes.
      </div>
      <Stack>
        <FormControl>
          <Stack direction={"row"} mb={5}>
            <FormLabel>Organization name</FormLabel>
            <Input
              type="text"
              // value={}
              // onChange={handleInputChange}
            />
            <Tooltip label="The legal name of your organization" fontSize="md">
              <QuestionIcon boxSize={5} />
            </Tooltip>
          </Stack>
          <Stack direction={"row"}>
            <FormLabel>Description</FormLabel>
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
              <QuestionIcon boxSize={5} />
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
    </Stack>
  );
};
export default OrganizationInfoForm;
