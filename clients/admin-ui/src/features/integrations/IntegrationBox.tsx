import { Box, Image, Flex, Button, Text, WarningIcon, CheckCircleIcon, InfoIcon } from "@fidesui/react";
import Tag from "~/features/common/Tag";
import { formatDate } from "~/features/common/utils";
const CONNECTOR_LOGOS_PATH = "/images/connector-logos/";
const FALLBACK_CONNECTOR_LOGOS_PATH = `${CONNECTOR_LOGOS_PATH}ethyca.svg`;


const IntegrationBox = (props: any) => {
  const {integration} = props;
  const renderLogo = () =>
    <Image
      boxSize="50px"
      objectFit="cover"
      src={FALLBACK_CONNECTOR_LOGOS_PATH}
      fallbackSrc={FALLBACK_CONNECTOR_LOGOS_PATH}
      alt={FALLBACK_CONNECTOR_LOGOS_PATH}
      {...props}
    />

  const renderLastTest = () => {
    const {last_test_succeeded: lastTestSucceded, last_test_timestamp: lastTestTimestamp} = integration;

    if (lastTestSucceded) {
      return (
        <Text color="green.700">
          <CheckCircleIcon boxSize="13px"/>
          Last connected {formatDate(lastTestTimestamp)}
        </Text>
      );
    }
    if (lastTestSucceded === false) {
      return (
        <Text color="red.700">
          <WarningIcon boxSize="13px"/>
          Error on {formatDate(lastTestTimestamp)}
        </Text>
      );
    }
    // lastTestSucceded === null
    return (
      <Text color="gray.700">
        <InfoIcon boxSize="13px"/>
        Never ran
      </Text>
    );
  }

  const renderIntegrationNameContainer = () =>
    <Flex direction="column" flexGrow={1} marginLeft="16px">
      <Text color="gray.700" fontWeight="semibold">{integration.name}</Text>
      {renderLastTest()}
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
