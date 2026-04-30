"use client";

import {
  ChakraBox as Box,
  ChakraHeading as Heading,
  ChakraStack as Stack,
  ChakraText as Text,
} from "fidesui";

import { useConfig } from "~/features/common/config.slice";
import {
  METRIC_COLUMNS,
  REQUEST_TYPE_LABELS,
  REQUEST_TYPE_ORDER,
  STATIC_ZERO_REQUEST_TYPES,
} from "~/features/privacy-request-metrics/constants";
import { useGetPrivacyRequestMetricsQuery } from "~/features/privacy-request-metrics/privacy-request-metrics.slice";
import type { RequestTypeMetrics } from "~/features/privacy-request-metrics/types";

function formatValue(value: number | null, key: string): string {
  if (value === null) {
    return "N/A";
  }
  if (key === "median_days_to_respond" || key === "mean_days_to_respond") {
    return String(value);
  }
  return value.toLocaleString();
}

const DEFAULT_METRICS_DESCRIPTION = `Disclosure published pursuant to California Civil Code \u00A7 1798.130(a)(5) and 11 CCR \u00A7 7102, and comparable state privacy laws. Figures reflect requests received from California Consumer Privacy Act (CCPA / CPRA) residents between {reportingPeriod}. A request is counted as \u201Cdenied\u201D when it was rejected in whole or in part because the identity of the requester could not be verified, the requester was not a consumer, the information requested was exempt from disclosure, or the request was otherwise invalid.`;

export const PrivacyRequestMetrics = () => {
  const config = useConfig();
  const { data, isLoading, isError } = useGetPrivacyRequestMetricsQuery();

  const metricsTitle =
    config.metrics?.title ?? "Privacy request disclosures";

  if (isError) {
    return (
      <Stack align="center" py={["6", "16"]} px={5} spacing={4}>
        <Heading as="h1" fontSize={["2xl", "3xl"]} fontWeight="semibold">
          {metricsTitle}
        </Heading>
        <Text color="gray.500" fontSize="sm">
          Unable to load disclosure metrics. Please try again later.
        </Text>
      </Stack>
    );
  }

  if (isLoading || !data) {
    return null;
  }

  // Merge API response with static zero rows (e.g., "limit" has no BE equivalent)
  const mergedTypes = { ...STATIC_ZERO_REQUEST_TYPES, ...data.request_types };

  // Order request types according to REQUEST_TYPE_ORDER, appending any extras
  const allKeys = Object.keys(mergedTypes);
  const orderedKeys = [
    ...REQUEST_TYPE_ORDER.filter((k) => allKeys.includes(k)),
    ...allKeys.filter((k) => !REQUEST_TYPE_ORDER.includes(k)),
  ];
  const requestTypes = orderedKeys.map(
    (k) => [k, mergedTypes[k]] as [string, RequestTypeMetrics],
  );

  return (
    <Stack align="center" py={["6", "16"]} px={5} spacing={10}>
      <Stack align="center" spacing={3} w="100%" maxWidth={1080}>
        <Heading as="h1" fontSize={["2xl", "3xl"]} fontWeight="semibold">
          {metricsTitle}
        </Heading>
        <Text color="gray.600" fontSize="sm">
          Reporting period: {data.reporting_period}
        </Text>
      </Stack>

      <Box w="100%" maxWidth={1080} overflowX="auto">
        <Box
          as="table"
          w="100%"
          fontSize={["xs", "sm"]}
          style={{ borderCollapse: "collapse" }}
        >
          <Box as="thead">
            <Box as="tr" borderBottomWidth="2px" borderColor="gray.200">
              <Box
                as="th"
                textAlign="left"
                py={3}
                px={3}
                fontWeight="semibold"
                color="gray.800"
              >
                Request type
              </Box>
              {METRIC_COLUMNS.map((col) => (
                <Box
                  key={col.key}
                  as="th"
                  textAlign="right"
                  py={3}
                  px={3}
                  fontWeight="semibold"
                  color="gray.800"
                >
                  {col.label}
                </Box>
              ))}
            </Box>
          </Box>
          <Box as="tbody">
            {requestTypes.map(([typeKey, metrics]) => (
              <Box
                key={typeKey}
                as="tr"
                borderBottomWidth="1px"
                borderColor="gray.100"
                _hover={{ bg: "gray.50" }}
              >
                <Box as="td" py={3} px={3} fontWeight="medium" color="gray.800">
                  {REQUEST_TYPE_LABELS[typeKey] ?? typeKey}
                </Box>
                {METRIC_COLUMNS.map((col) => (
                  <Box
                    key={col.key}
                    as="td"
                    textAlign="right"
                    py={3}
                    px={3}
                    color="gray.700"
                  >
                    {formatValue(
                      metrics[col.key as keyof RequestTypeMetrics],
                      col.key,
                    )}
                  </Box>
                ))}
              </Box>
            ))}
          </Box>
        </Box>
      </Box>

      <Box w="100%" maxWidth={1080} borderRadius="md" p={5}>
        <Text color="gray.500" fontSize="xs">
          {(
            config.metrics?.description ?? DEFAULT_METRICS_DESCRIPTION
          ).replace("{reportingPeriod}", data.reporting_period)}
        </Text>
      </Box>
    </Stack>
  );
};
