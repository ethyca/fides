import {
  Box,
  Button,
  CheckCircleIcon,
  ErrorWarningIcon,
  Flex,
  InfoIcon,
  Text,
} from "fidesui";
import NextLink from "next/link";

import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/v2/routes";
import Tag from "~/features/common/Tag";
import { formatDate } from "~/features/common/utils";
import ConnectionTypeLogo from "~/features/datastore-connections/ConnectionTypeLogo";

const BIGQUERY_TAGS = [
  "Data Warehouse",
  "BigQuery",
  "Discovery",
  "Inventory",
];

const IntegrationBox = (props: any) => {
  const {integration} = props;
  const renderLogo = () =>
    <ConnectionTypeLogo data={integration} boxSize="50px"/>

  const renderLastTest = () => {
    const {last_test_succeeded: lastTestSucceded, last_test_timestamp: lastTestTimestamp} = integration;

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
          <ErrorWarningIcon boxSize="13px" marginRight="4px"/>
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
      <Text color="gray.700" fontWeight="semibold">{integration.name || "(No name)"}</Text>
      {renderLastTest()}
    </Flex>

  const renderManageButton = () =>
    <NextLink href={`${INTEGRATION_MANAGEMENT_ROUTE}/bigquery_connection_${integration.key}`}>
      <Button
        size="sm"
        variant="outline"
      >
        Manage
      </Button>
    </NextLink>

  const renderTags = () =>
    <>
      {BIGQUERY_TAGS.map((item) => <Tag key={item}>{item}</Tag>)}
    </>

  return (
    <Box maxW='760px' borderWidth={1} borderRadius='lg' overflow='hidden' height="114px" padding="12px" marginBottom="24px">
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
