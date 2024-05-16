import { Box, Image, Flex, Button, Text, Tag, WarningIcon } from "@fidesui/react";
const CONNECTOR_LOGOS_PATH = "/images/connector-logos/";
const FALLBACK_CONNECTOR_LOGOS_PATH = `${CONNECTOR_LOGOS_PATH}ethyca.svg`;


const FidesTag = (props) =>
  <Tag
    borderRadius="2px"
    padding="4px 8px"
    bg="#EDF2F7"
    color="#4A5568"
    marginRight="4px">
      {props.children}
  </Tag>

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
      <Text>
        System detection -> BigQuery
      </Text>
      <Text color="#9B2C2C">
        <WarningIcon boxSize="13px" color="#C53030"/>
        Error on August 4, 2021, 09:35:46 PST
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
      <FidesTag>Cloud</FidesTag>
      <FidesTag>GCP</FidesTag>
      <FidesTag>BigQuery</FidesTag>
      <FidesTag>Discovery</FidesTag>
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
