import {
  Button,
  ChakraBox as Box,
  ChakraDivider as Divider,
  ChakraFlex as Flex,
  ChakraHStack as HStack,
  ChakraText as Text,
  ChakraVStack as VStack,
  CUSTOM_TAG_COLOR,
  Drawer,
  Icons,
  Tag,
} from "fidesui";

import { MockDataset } from "./mock-data";

type ResultStatus = "reached" | "failed" | "skipped";

interface CollectionResult {
  name: string;
  status: ResultStatus;
  via?: string; // traversal path hint
  reason?: string;
}

const STATUS_TAG: Record<
  ResultStatus,
  { label: string; color: CUSTOM_TAG_COLOR; icon: React.ReactNode }
> = {
  reached: {
    label: "Reached",
    color: CUSTOM_TAG_COLOR.SUCCESS,
    icon: <Icons.CheckmarkFilled size={12} />,
  },
  failed: {
    label: "Failed",
    color: CUSTOM_TAG_COLOR.ERROR,
    icon: <Icons.WarningAlt size={12} />,
  },
  skipped: {
    label: "Skipped",
    color: CUSTOM_TAG_COLOR.DEFAULT,
    icon: <Icons.ViewOff size={12} />,
  },
};

const RESULTS_BY_DATASET: Record<string, CollectionResult[]> = {
  legacy_orders_pg: [
    { name: "users", status: "reached", via: "identity → email" },
    { name: "orders", status: "reached", via: "FK → users.id" },
    { name: "order_items", status: "reached", via: "FK → orders.id" },
    { name: "addresses", status: "failed", reason: "No FK to a reachable collection (user_id is unlabeled)" },
    { name: "payments", status: "reached", via: "FK → orders.id" },
    { name: "refunds", status: "reached", via: "FK → orders.id" },
    { name: "shipments", status: "reached", via: "FK → orders.id" },
    { name: "tax_records", status: "reached", via: "FK → orders.id" },
    { name: "promotions", status: "reached", via: "FK → orders.id" },
    { name: "carts", status: "skipped", reason: "skip_processing = true" },
    { name: "audit_log", status: "skipped", reason: "skip_processing = true" },
  ],
};

const SectionHeading = ({ children }: { children: React.ReactNode }) => (
  <Text
    fontSize="sm"
    fontWeight="700"
    textTransform="uppercase"
    color="gray.700"
    letterSpacing="wide"
    mb={2}
  >
    {children}
  </Text>
);

const Stat = ({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) => (
  <VStack spacing={0} align="flex-start" minW="80px">
    <Text fontSize="2xl" fontWeight="700" color={color} lineHeight="1.1">
      {value}
    </Text>
    <Text fontSize="xs" color="gray.600" textTransform="uppercase" letterSpacing="wide">
      {label}
    </Text>
  </VStack>
);

interface TryDsrDrawerProps {
  open: boolean;
  onClose: () => void;
  dataset: MockDataset;
  onFixFailures?: (collectionName: string) => void;
}

export const TryDsrDrawer = ({
  open,
  onClose,
  dataset,
  onFixFailures,
}: TryDsrDrawerProps) => {
  const results =
    RESULTS_BY_DATASET[dataset.fidesKey] ??
    RESULTS_BY_DATASET.legacy_orders_pg;

  const reached = results.filter((r) => r.status === "reached").length;
  const failed = results.filter((r) => r.status === "failed").length;
  const skipped = results.filter((r) => r.status === "skipped").length;
  const allOk = failed === 0;

  const failedCollection = results.find((r) => r.status === "failed");

  return (
    <Drawer
      open={open}
      onClose={onClose}
      width={620}
      title={
        <HStack spacing={2}>
          <Icons.Launch />
          <span>Try DSR result for</span>
          <Tag color={CUSTOM_TAG_COLOR.MARBLE}>{dataset.fidesKey}</Tag>
        </HStack>
      }
      footer={
        <Flex justify="space-between" gap={2} w="100%" align="center">
          <Text fontSize="xs" color="gray.500">
            Synthetic run · no real data was fetched · 2026-05-06 14:02
          </Text>
          <HStack spacing={2}>
            <Button onClick={onClose}>Close</Button>
            <Button type="primary" icon={<Icons.Renew />}>
              Re-run
            </Button>
          </HStack>
        </Flex>
      }
      data-testid="try-dsr-drawer"
    >
      <VStack spacing={5} align="stretch">
        <Box
          p={3}
          borderRadius="sm"
          bg={allOk ? "green.50" : "red.50"}
          borderLeft="3px solid"
          borderColor={allOk ? "green.500" : "red.400"}
        >
          <HStack spacing={2} mb={1}>
            {allOk ? (
              <Icons.CheckmarkFilled
                color="var(--chakra-colors-green-500)"
              />
            ) : (
              <Icons.WarningAlt color="var(--chakra-colors-red-500)" />
            )}
            <Text
              fontSize="sm"
              fontWeight="700"
              color={allOk ? "green.800" : "red.700"}
            >
              {allOk
                ? "All collections reachable"
                : `${failed} collection${failed === 1 ? "" : "s"} failed to reach`}
            </Text>
          </HStack>
          <Text fontSize="sm" color={allOk ? "green.700" : "red.700"}>
            {allOk
              ? "This dataset is ready for a real Access DSR."
              : "A real DSR against this dataset would not return data for the failed collections."}
          </Text>
        </Box>

        <Box>
          <SectionHeading>Synthetic identity</SectionHeading>
          <HStack
            spacing={2}
            p={2.5}
            border="1px solid"
            borderColor="gray.200"
            borderRadius="sm"
            bg="gray.50"
          >
            <Icons.User size={14} />
            <Text fontFamily="mono" fontSize="sm">
              email = test+akshay@ethyca.com
            </Text>
          </HStack>
          <Text fontSize="xs" color="gray.500" mt={1}>
            No real subject record was queried.
          </Text>
        </Box>

        <HStack spacing={6}>
          <Stat label="Reached" value={reached} color="green.600" />
          <Stat label="Failed" value={failed} color="red.500" />
          <Stat label="Skipped" value={skipped} color="gray.500" />
          <Stat label="Total" value={results.length} color="gray.700" />
        </HStack>

        <Divider />

        <Box>
          <SectionHeading>Traversal path</SectionHeading>
          <Box
            p={3}
            border="1px solid"
            borderColor="gray.200"
            borderRadius="sm"
            bg="gray.50"
            fontFamily="mono"
            fontSize="xs"
            lineHeight="1.7"
            color="gray.700"
          >
            <Text>email → users (identity)</Text>
            <Text pl={4}>└─ orders (FK users.id)</Text>
            <Text pl={8}>├─ order_items (FK orders.id)</Text>
            <Text pl={8}>├─ payments (FK orders.id)</Text>
            <Text pl={8}>├─ refunds (FK orders.id)</Text>
            <Text pl={8}>├─ shipments (FK orders.id)</Text>
            <Text pl={8}>├─ tax_records (FK orders.id)</Text>
            <Text pl={8}>└─ promotions (FK orders.id)</Text>
            <Text pl={4} color="red.500">└─ addresses ✗ (no usable FK)</Text>
            <Text color="gray.400" mt={1}>
              [skipped] carts · audit_log
            </Text>
          </Box>
        </Box>

        <Box>
          <SectionHeading>Per-collection results</SectionHeading>
          <VStack spacing={1} align="stretch">
            {results.map((r) => (
              <Flex
                key={r.name}
                align="center"
                gap={3}
                px={3}
                py={2}
                borderRadius="sm"
                bg={
                  r.status === "failed"
                    ? "red.50"
                    : r.status === "skipped"
                    ? "gray.50"
                    : "white"
                }
                border="1px solid"
                borderColor={
                  r.status === "failed" ? "red.200" : "gray.200"
                }
                data-testid={`result-${r.name}`}
              >
                <Box minW="140px">
                  <Text fontSize="sm" fontWeight="600" fontFamily="mono">
                    {r.name}
                  </Text>
                </Box>
                <Box minW="100px">
                  <Tag color={STATUS_TAG[r.status].color}>
                    <HStack spacing={1}>
                      {STATUS_TAG[r.status].icon}
                      <span>{STATUS_TAG[r.status].label}</span>
                    </HStack>
                  </Tag>
                </Box>
                <Box flex={1}>
                  <Text fontSize="xs" color="gray.600">
                    {r.via ?? r.reason ?? "—"}
                  </Text>
                </Box>
                {r.status === "failed" && (
                  <Button
                    size="small"
                    icon={<Icons.Settings />}
                    onClick={() => onFixFailures?.(r.name)}
                    data-testid={`fix-${r.name}`}
                  >
                    Fix
                  </Button>
                )}
              </Flex>
            ))}
          </VStack>
        </Box>

        {failedCollection && (
          <Box
            p={3}
            borderRadius="sm"
            bg="red.50"
            borderLeft="3px solid"
            borderColor="red.400"
          >
            <HStack spacing={2} mb={1}>
              <Icons.WarningAlt color="var(--chakra-colors-red-500)" />
              <Text fontSize="sm" fontWeight="700" color="red.700">
                Fix failures
              </Text>
            </HStack>
            <Text fontSize="sm" color="red.700">
              Wire {failedCollection.name} so it has a usable identity or FK
              link, then re-run.
            </Text>
            <Button
              type="primary"
              icon={<Icons.Settings />}
              size="small"
              mt={2}
              onClick={() => onFixFailures?.(failedCollection.name)}
            >
              Open wiring drawer for {failedCollection.name}
            </Button>
          </Box>
        )}
      </VStack>
    </Drawer>
  );
};
