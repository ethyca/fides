import { Box, Image, Flex, Button, Text, WarningIcon, CheckCircleIcon } from "@fidesui/react";
import Tag from "~/features/common/Tag";
const CONNECTOR_LOGOS_PATH = "/images/connector-logos/";
const FALLBACK_CONNECTOR_LOGOS_PATH = `${CONNECTOR_LOGOS_PATH}ethyca.svg`;


const IntegrationBox = (props) => {
  const renderLogo = () =>
    <Image
      boxSize="50px"
      objectFit="cover"
      src={FALLBACK_CONNECTOR_LOGOS_PATH}
      fallbackSrc={FALLBACK_CONNECTOR_LOGOS_PATH}
      alt={FALLBACK_CONNECTOR_LOGOS_PATH}
      {...props}
    />

  const renderIntegrationNameContainer = () =>
    <Flex direction="column" flexGrow={1} marginLeft="16px">
      <Text color="gray.700" fontWeight="semibold">BigQuery</Text>
      <Text color="green.700">
        <CheckCircleIcon boxSize="13px"/>
        Error on August 4, 2021, 09:35:46 PST {/* last_test_timestamp and last_test_succeeded */}
      </Text>
      <Text color="red.700">
        <WarningIcon boxSize="13px"/>
        Error on August 4, 2021, 09:35:46 PST {/* last_test_timestamp and last_test_succeeded */}
      </Text>
    </Flex>

  const renderManageButton = () =>
    <Button
      justifySelf="self-end"
      size="xs"
      variant="outline"
      onClick={() => {

      }}
      loadingText="Manage"
      spinnerPlacement="end"
    >
      Manage
    </Button>

  const renderTags = () =>
    <>
      <Tag>Cloud</Tag>
      <Tag>GCP</Tag>
      <Tag>BigQuery</Tag>
      <Tag>Discovery</Tag>
    </>

  return (
    <Box maxW='760px' borderWidth={1} borderRadius='lg' overflow='hidden' height="114px" padding="12px">
      <Flex>
        {renderLogo()}
        {renderIntegrationNameContainer()}
        {renderManageButton()}
      </Flex>
      <Flex marginTop="16px">
        {renderTags()}
      </Flex>
    </Box>
  );
}

export default IntegrationBox;
