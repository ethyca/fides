import {
  Box,
  Button,
  ButtonGroup,
  Flex,
  Heading,
  IconButton,
  NotAllowedIcon,
  Spacer,
  Text,
} from "@fidesui/react";
import BackButton from "~/features/common/nav/v2/BackButton";
import { PRIVACY_EXPERIENCE_ROUTE } from "~/features/common/nav/v2/routes";

const ConfigurePrivacyExperience = () => (
  <Flex w="full" h="full" direction="row">
    <Flex direction="column" h="full" w="25%" borderRight="1px solid #DEE5EE">
      <Flex direction="column" h="full" overflow="scroll" pl={4}>
        <BackButton backPath={PRIVACY_EXPERIENCE_ROUTE} mt={4} />
        <Heading fontSize="md" fontWeight="semibold" mb={4}>
          Configure experience
        </Heading>
        <Text>Coming soon</Text>
      </Flex>
      <Spacer />
      <ButtonGroup size="sm" borderTop="1px solid #DEE5EE" p={4}>
        <Button variant="outline">Cancel</Button>
        <Button colorScheme="primary">Save</Button>
      </ButtonGroup>
    </Flex>
    <Flex direction="column" w="75%" bgColor="gray.50">
      <Flex
        direction="row"
        p={4}
        align="center"
        bgColor="white"
        borderBottom="1px solid #DEE5EE"
      >
        <Text fontSize="md" fontWeight="semibold">
          PREVIEW
        </Text>
        <Spacer />
        <ButtonGroup size="sm" variant="outline" isAttached>
          <IconButton
            // TODO: replace with "mobile" icon
            icon={<NotAllowedIcon />}
            aria-label={"View mobile preview"}
          />
          <IconButton
            // TODO: replace with "desktop" icon
            icon={<NotAllowedIcon />}
            aria-label={"View desktop preview"}
          />
        </ButtonGroup>
      </Flex>
    </Flex>
  </Flex>
);

export default ConfigurePrivacyExperience;
