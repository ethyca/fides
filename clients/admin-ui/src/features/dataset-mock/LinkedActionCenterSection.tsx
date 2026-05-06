import {
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
import NextLink from "next/link";

import { HealthBadge, MockDataset } from "./mock-data";

const SectionLabel = ({ children }: { children: React.ReactNode }) => (
  <Text
    fontSize="xs"
    textTransform="uppercase"
    letterSpacing="wide"
    color="gray.500"
    fontWeight="600"
    mb={1}
  >
    {children}
  </Text>
);

interface LinkedSibling {
  fidesKey: string;
  name: string;
  badges: HealthBadge[];
}

const SIBLINGS_BY_MONITOR: Record<string, LinkedSibling[]> = {
  legacy_postgres_monitor: [
    {
      fidesKey: "legacy_orders_pg_replica",
      name: "Legacy Orders (read replica)",
      badges: ["healthy"],
    },
    {
      fidesKey: "legacy_orders_audit",
      name: "Legacy Orders Audit Schema",
      badges: ["needs-dsr-wiring"],
    },
  ],
};

const HEALTH_LABELS: Record<HealthBadge, { label: string; color: CUSTOM_TAG_COLOR }> = {
  "needs-dsr-wiring": { label: "Needs DSR wiring", color: CUSTOM_TAG_COLOR.ERROR },
  "connection-failed": { label: "Connection failed", color: CUSTOM_TAG_COLOR.ERROR },
  "connection-untested": { label: "Connection untested", color: CUSTOM_TAG_COLOR.ERROR },
  "schema-drifted": { label: "Schema drifted", color: CUSTOM_TAG_COLOR.CAUTION },
  "monitor-disabled": { label: "Monitor disabled", color: CUSTOM_TAG_COLOR.CAUTION },
  "no-successful-dsr": { label: "No successful DSR", color: CUSTOM_TAG_COLOR.CAUTION },
  manual: { label: "Manual", color: CUSTOM_TAG_COLOR.DEFAULT },
  healthy: { label: "Healthy", color: CUSTOM_TAG_COLOR.SUCCESS },
};

interface LinkedActionCenterSectionProps {
  dataset: MockDataset;
}

export const LinkedActionCenterSection = ({
  dataset,
}: LinkedActionCenterSectionProps) => {
  if (!dataset.sourceMonitor) {
    return null;
  }

  const siblings =
    SIBLINGS_BY_MONITOR[dataset.sourceMonitor] ?? [];
  const monitorHref = `/data-discovery/action-center/datastore/${encodeURIComponent(
    dataset.sourceMonitor,
  )}`;

  return (
    <Box
      bg="white"
      border="1px solid"
      borderColor="gray.200"
      borderRadius="md"
      p={5}
      mb={4}
      data-testid="linked-action-center"
    >
      <HStack spacing={2} mb={3}>
        <Icons.Activity size={16} />
        <Text fontSize="md" fontWeight="700">
          Linked Action Center provenance
        </Text>
      </HStack>

      <Flex gap={8} align="flex-start" wrap="wrap">
        <Box minW="240px">
          <SectionLabel>Source monitor</SectionLabel>
          <NextLink href={monitorHref} passHref legacyBehavior>
            <a>
              <HStack spacing={2}>
                <Icons.DataTable size={14} />
                <Text
                  fontSize="sm"
                  color="blue.600"
                  fontWeight="600"
                  fontFamily="mono"
                  _hover={{ textDecoration: "underline" }}
                >
                  {dataset.sourceMonitor}
                </Text>
                <Icons.Launch size={12} color="var(--chakra-colors-blue-600)" />
              </HStack>
            </a>
          </NextLink>
          <Text fontSize="xs" color="gray.500" mt={1}>
            Discovers and classifies fields in this dataset.
          </Text>
        </Box>

        <Box minW="240px">
          <SectionLabel>Approval</SectionLabel>
          <HStack spacing={2}>
            <Icons.CheckmarkFilled
              size={14}
              color="var(--chakra-colors-green-500)"
            />
            <Text fontSize="sm" fontWeight="600">
              {dataset.approvedBy}
            </Text>
          </HStack>
          <Text fontSize="xs" color="gray.500" mt={1}>
            {dataset.approvalAction} · {dataset.approvedAt}
          </Text>
        </Box>

        <Box minW="240px" flex={1}>
          <SectionLabel>
            Linked datasets ({siblings.length} sharing this monitor)
          </SectionLabel>
          {siblings.length === 0 ? (
            <Text fontSize="sm" color="gray.500">
              No other datasets share this monitor.
            </Text>
          ) : (
            <VStack align="stretch" spacing={1.5}>
              {siblings.map((s) => (
                <HStack
                  key={s.fidesKey}
                  justify="space-between"
                  spacing={2}
                  px={2}
                  py={1.5}
                  borderRadius="sm"
                  bg="gray.50"
                  _hover={{ bg: "gray.100" }}
                  data-testid={`sibling-${s.fidesKey}`}
                >
                  <HStack spacing={2}>
                    <Icons.Layers size={12} />
                    <Text fontSize="sm" fontWeight="600" fontFamily="mono">
                      {s.fidesKey}
                    </Text>
                  </HStack>
                  <HStack spacing={1}>
                    {s.badges.map((b) => (
                      <Tag key={b} color={HEALTH_LABELS[b].color}>
                        {HEALTH_LABELS[b].label}
                      </Tag>
                    ))}
                  </HStack>
                </HStack>
              ))}
            </VStack>
          )}
        </Box>
      </Flex>

      <Divider my={4} />

      <HStack spacing={2}>
        <Icons.Information size={12} color="var(--chakra-colors-gray-500)" />
        <Text fontSize="xs" color="gray.600">
          {dataset.linkedActionCenterItems > 0
            ? `${dataset.linkedActionCenterItems} approval action${dataset.linkedActionCenterItems === 1 ? "" : "s"} contributed to this dataset.`
            : "No Action Center activity recorded for this dataset."}
        </Text>
      </HStack>
    </Box>
  );
};
