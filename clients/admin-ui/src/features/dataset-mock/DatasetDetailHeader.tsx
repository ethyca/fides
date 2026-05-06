import {
  Button,
  ChakraBox as Box,
  ChakraDivider as Divider,
  ChakraFlex as Flex,
  ChakraHStack as HStack,
  ChakraText as Text,
  ChakraVStack as VStack,
  CUSTOM_TAG_COLOR,
  Icons,
  Tag,
} from "fidesui";

import { HealthBadges } from "./HealthBadges";
import { MockDataset } from "./mock-data";

interface StatTileProps {
  label: string;
  value: string | number;
  testid?: string;
}

const StatTile = ({ label, value, testid }: StatTileProps) => (
  <VStack
    align="flex-start"
    spacing={1}
    minW="140px"
    data-testid={testid}
  >
    <Text
      fontSize="xs"
      textTransform="uppercase"
      letterSpacing="wide"
      color="gray.500"
      fontWeight="600"
    >
      {label}
    </Text>
    <Text fontSize="2xl" fontWeight="600" lineHeight="1.1">
      {value}
    </Text>
  </VStack>
);

interface DatasetDetailHeaderProps {
  dataset: MockDataset;
  onTryDsr?: () => void;
}

export const DatasetDetailHeader = ({
  dataset,
  onTryDsr,
}: DatasetDetailHeaderProps) => (
  <Box
    bg="white"
    border="1px solid"
    borderColor="gray.200"
    borderRadius="md"
    p={5}
    mb={4}
    data-testid="dataset-detail-header"
  >
    <Flex justify="space-between" align="flex-start" mb={3} gap={4}>
      <VStack align="flex-start" spacing={2} flex={1} minW={0}>
        <HStack spacing={2} align="center">
          <Text fontSize="xl" fontWeight="700" lineHeight="1.2">
            {dataset.name}
          </Text>
          <Tag color={CUSTOM_TAG_COLOR.MARBLE}>{dataset.fidesKey}</Tag>
          {dataset.integration ? (
            <Tag color={CUSTOM_TAG_COLOR.INFO}>
              <HStack spacing={1}>
                <Icons.Link size={12} />
                <span>{dataset.integration}</span>
              </HStack>
            </Tag>
          ) : (
            <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>No integration</Tag>
          )}
        </HStack>
        <Text fontSize="sm" color="gray.600">
          {dataset.description}
        </Text>
        <HealthBadges badges={dataset.healthBadges} />
      </VStack>

      <HStack spacing={2}>
        <Button
          icon={<Icons.Launch />}
          type="primary"
          onClick={onTryDsr}
          data-testid="try-dsr-btn"
        >
          Try DSR
        </Button>
      </HStack>
    </Flex>

    <Divider mb={3} />

    <HStack spacing={8} align="flex-start">
      <StatTile
        label="Collections"
        value={dataset.collectionCount}
        testid="stat-collections"
      />
      <StatTile
        label="Total fields"
        value={dataset.totalFields}
        testid="stat-fields"
      />
      <StatTile
        label="Approved"
        value={`${dataset.approvedFieldPct}%`}
        testid="stat-approved"
      />
      <StatTile
        label="Last classified"
        value={dataset.lastClassifiedAt}
        testid="stat-last-classified"
      />
      <StatTile
        label="Action Center items"
        value={dataset.linkedActionCenterItems}
        testid="stat-ac-items"
      />
    </HStack>
  </Box>
);
