"use client";

import { useEffect, useState } from "react";
import {
  ChakraBox as Box,
  ChakraFlex as Flex,
  ChakraHeading as Heading,
  ChakraStack as Stack,
  ChakraText as Text,
} from "fidesui";
import { useSelector } from "react-redux";

import {
  METRIC_COLUMNS,
  REQUEST_TYPE_LABELS,
} from "~/features/privacy-request-metrics/constants";
import type { RequestTypeMetrics } from "~/features/privacy-request-metrics/types";
import { useGetPrivacyRequestMetrics } from "~/features/privacy-request-metrics/useGetPrivacyRequestMetrics";
import { selectConsentState } from "~/features/consent/consent.slice";
import type { LocationOption } from "~/app/server-utils/fetchLocationsFromApi";

const ALL_LOCATIONS_VALUE = "";

/**
 * Convert a location ID from the locations API format (e.g. "us_ca")
 * to the ISO format used by the metrics API (e.g. "US-CA").
 */
function locationIdToIso(id: string): string {
  const parts = id.split("_");
  if (parts.length === 1) {
    return parts[0].toUpperCase();
  }
  return `${parts[0].toUpperCase()}-${parts.slice(1).join("_").toUpperCase()}`;
}

/**
 * Convert an ISO location (e.g. "US-CA") to the locations API format (e.g. "us_ca").
 */
function isoToLocationId(iso: string): string {
  return iso.toLowerCase().replace(/-/g, "_");
}

function formatValue(value: number | null, key: string): string {
  if (value === null) {
    return "N/A";
  }
  if (key === "median_days_to_respond" || key === "mean_days_to_respond") {
    return String(value);
  }
  return value.toLocaleString();
}

interface PrivacyRequestMetricsProps {
  locationOptions: LocationOption[];
}

export const PrivacyRequestMetrics = ({
  locationOptions,
}: PrivacyRequestMetricsProps) => {
  // currentGeo is already in underscore format from the server (e.g., "us_ca")
  const { location: currentGeo } = useSelector(selectConsentState);

  const [selectedLocation, setSelectedLocation] =
    useState<string>(ALL_LOCATIONS_VALUE);
  const [hasAutoSelected, setHasAutoSelected] = useState(false);

  // Auto-select the user's geo when it becomes available (after hydration)
  useEffect(() => {
    if (hasAutoSelected || !currentGeo) {
      return;
    }
    const matchesOption = locationOptions.some((o) => o.id === currentGeo);
    if (matchesOption) {
      setSelectedLocation(currentGeo);
    }
    setHasAutoSelected(true);
  }, [currentGeo, locationOptions, hasAutoSelected]);

  const locationParam = selectedLocation
    ? locationIdToIso(selectedLocation)
    : undefined;
  const { data, isLoading } = useGetPrivacyRequestMetrics(locationParam);

  if (isLoading || !data) {
    return null;
  }

  const requestTypes = Object.entries(data.request_types);

  return (
    <Stack align="center" py={["6", "16"]} px={5} spacing={10}>
      <Stack align="center" spacing={3} w="100%" maxWidth={960}>
        <Heading as="h1" fontSize={["2xl", "3xl"]} fontWeight="semibold">
          Privacy request disclosures
        </Heading>
        <Text color="gray.600" fontSize="sm">
          Reporting period: {data.reporting_period}
        </Text>
      </Stack>

      {locationOptions.length > 0 && (
        <Flex w="100%" maxWidth={960} justifyContent="flex-end">
          <Box
            as="select"
            value={selectedLocation}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
              setSelectedLocation(e.target.value)
            }
            px={3}
            py={2}
            borderWidth="1px"
            borderColor="gray.200"
            borderRadius="md"
            fontSize="sm"
            color="gray.700"
            bg="white"
            cursor="pointer"
            _hover={{ borderColor: "gray.300" }}
          >
            <option value={ALL_LOCATIONS_VALUE}>All locations</option>
            {locationOptions.map((option) => (
              <option key={option.id} value={option.id}>
                {option.name}
              </option>
            ))}
          </Box>
        </Flex>
      )}

      <Box w="100%" maxWidth={960} overflowX="auto">
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
                <Box
                  as="td"
                  py={3}
                  px={3}
                  fontWeight="medium"
                  color="gray.800"
                >
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

      <Flex w="100%" maxWidth={960} justifyContent="center">
        <Text color="gray.500" fontSize="xs" textAlign="center">
          Disclosed pursuant to the California Consumer Privacy Act (CCPA) and
          California Privacy Rights Act (CPRA), Cal. Code Regs. tit. 11, &sect;
          7102.
        </Text>
      </Flex>
    </Stack>
  );
};
