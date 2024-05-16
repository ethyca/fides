import { Box, Image, Flex, Button, Text, WarningTwoIcon, CheckCircleIcon, InfoIcon } from "@fidesui/react";
import Tag from "~/features/common/Tag";
import { formatDate } from "~/features/common/utils";
const CONNECTOR_LOGOS_PATH = "/images/connector-logos/";
const FALLBACK_CONNECTOR_LOGOS_PATH = `${CONNECTOR_LOGOS_PATH}ethyca.svg`;
import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/v2/routes";
import NextLink from "next/link";

const BIGQUERY_TAGS = [
  "Cloud",
  "GCP",
  "BigQuery",
  "Discovery",
];

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
    // lastTestSucceded = null;
    // lastTestTimestamp = "2024-05-16T17:59:21+0000";

    if (lastTestSucceded) {
      return (
        <Flex alignItems="center" color="green.500" >
          <CheckCircleIcon boxSize="13px" marginRight="4px"/>
          Last connected {formatDate(lastTestTimestamp)}
        </Flex>
      );
    }

    if (lastTestSucceded === false) {
      return (
        <Flex alignItems="center" color="red.600" >
          <WarningTwoIcon boxSize="13px" marginRight="4px"/>
          Error on {formatDate(lastTestTimestamp)}
        </Flex>
      );
    }

    return (
      <Flex alignItems="center" color="gray.600" >
        <InfoIcon boxSize="13px" marginRight="4px"/>
        Never ran
      </Flex>
    );
  }

  const renderIntegrationNameContainer = () =>
    <Flex direction="column" flexGrow={1} marginLeft="16px">
      <Text color="gray.700" fontWeight="semibold">{integration.name}</Text>
      {renderLastTest()}
    </Flex>

  const renderManageButton = () =>
    <NextLink href={`${INTEGRATION_MANAGEMENT_ROUTE}/bigquery_connection_${integration.key}`}>
      <Button
        justifySelf="self-end"
        size="xs"
        variant="outline"
        loadingText="Manage"
        spinnerPlacement="end"
      >
        Manage
      </Button>
    </NextLink>

  const renderTags = () =>
    <>
      {BIGQUERY_TAGS.map((item) => <Tag key={item}>{item}</Tag>)}
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
