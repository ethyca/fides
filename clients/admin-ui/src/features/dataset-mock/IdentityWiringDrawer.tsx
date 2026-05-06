import {
  Button,
  ChakraBox as Box,
  ChakraFlex as Flex,
  ChakraHStack as HStack,
  ChakraText as Text,
  ChakraVStack as VStack,
  CUSTOM_TAG_COLOR,
  Drawer,
  Icons,
  Radio,
  Select,
  SparkleIcon,
  Tag,
} from "fidesui";
import { useState } from "react";

import {
  MOCK_COLLECTION_DETAILS,
  MockField,
} from "./mock-tree-data";

interface IdentityWiringDrawerProps {
  open: boolean;
  onClose: () => void;
  collectionKey: string;
}

type Mode = "identity" | "fk";

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

const FieldOption = ({
  field,
  selected,
  onSelect,
}: {
  field: MockField;
  selected: boolean;
  onSelect: () => void;
}) => (
  <Box
    onClick={onSelect}
    cursor="pointer"
    px={3}
    py={2.5}
    borderRadius="sm"
    border="1px solid"
    borderColor={selected ? "blue.400" : "gray.200"}
    bg={selected ? "blue.50" : field.isIdentityCandidate ? "yellow.50" : "white"}
    _hover={{ borderColor: selected ? "blue.500" : "gray.300" }}
    data-testid={`identity-option-${field.name}`}
  >
    <Flex align="center" gap={3}>
      <Radio checked={selected} />
      <Box flex={1}>
        <HStack spacing={2}>
          <Text fontWeight="600" fontSize="sm">
            {field.name}
          </Text>
          <Text fontSize="xs" color="gray.500" fontFamily="mono">
            {field.type}
          </Text>
          {field.isIdentityCandidate && (
            <Tag color={CUSTOM_TAG_COLOR.NECTAR}>
              <HStack spacing={1}>
                <SparkleIcon size={10} />
                <span>Metis recommends</span>
              </HStack>
            </Tag>
          )}
        </HStack>
        {field.dataCategories.length > 0 && (
          <HStack spacing={1} mt={1}>
            {field.dataCategories.map((c) => (
              <Tag key={c} color={CUSTOM_TAG_COLOR.MARBLE}>
                {c}
              </Tag>
            ))}
          </HStack>
        )}
      </Box>
    </Flex>
  </Box>
);

export const IdentityWiringDrawer = ({
  open,
  onClose,
  collectionKey,
}: IdentityWiringDrawerProps) => {
  const collection =
    MOCK_COLLECTION_DETAILS[collectionKey] ?? MOCK_COLLECTION_DETAILS.users;

  const [mode, setMode] = useState<Mode>("identity");
  // Pre-select email so the screenshot shows a meaningful state.
  const [selectedField, setSelectedField] = useState<string>("email");
  const [parentCollection, setParentCollection] = useState<string>("orders");
  const [parentFkField, setParentFkField] = useState<string>("user_id");
  const [applied, setApplied] = useState(false);

  const candidates = collection.fields;
  const sortedCandidates = [...candidates].sort((a, b) => {
    if (a.isIdentityCandidate && !b.isIdentityCandidate) {
      return -1;
    }
    if (!a.isIdentityCandidate && b.isIdentityCandidate) {
      return 1;
    }
    return 0;
  });

  return (
    <Drawer
      open={open}
      onClose={onClose}
      width={520}
      title={
        <HStack spacing={2}>
          <Icons.Settings />
          <span>Wire DSR for</span>
          <Tag color={CUSTOM_TAG_COLOR.MARBLE}>{collection.name}</Tag>
          <Tag color={CUSTOM_TAG_COLOR.ERROR}>Needs DSR wiring</Tag>
        </HStack>
      }
      footer={
        <Flex justify="flex-end" gap={2} w="100%">
          <Button onClick={onClose}>Cancel</Button>
          <Button
            type="primary"
            onClick={() => setApplied(true)}
            data-testid="apply-wiring-btn"
          >
            Apply &amp; revalidate
          </Button>
        </Flex>
      }
      data-testid="identity-wiring-drawer"
    >
      <VStack spacing={5} align="stretch">
        <Box
          p={3}
          borderRadius="sm"
          bg="red.50"
          borderLeft="3px solid"
          borderColor="red.400"
        >
          <HStack spacing={2}>
            <Icons.WarningAlt color="var(--chakra-colors-red-500)" />
            <Text fontSize="sm" color="red.700">
              {collection.reason ??
                "This collection is not reachable by any DSR identity."}
            </Text>
          </HStack>
        </Box>

        <Box>
          <SectionHeading>Choose how to make this collection reachable</SectionHeading>
          <Flex gap={2} mt={2}>
            <Button
              type={mode === "identity" ? "primary" : "default"}
              onClick={() => setMode("identity")}
              icon={<Icons.User />}
              data-testid="mode-identity"
            >
              Declare an identity field
            </Button>
            <Button
              type={mode === "fk" ? "primary" : "default"}
              onClick={() => setMode("fk")}
              icon={<Icons.Link />}
              data-testid="mode-fk"
            >
              Link to a reachable parent
            </Button>
          </Flex>
        </Box>

        {mode === "identity" ? (
          <Box>
            <SectionHeading>Pick the field that identifies a user</SectionHeading>
            <VStack spacing={2} align="stretch">
              {sortedCandidates.map((f) => (
                <FieldOption
                  key={f.name}
                  field={f}
                  selected={selectedField === f.name}
                  onSelect={() => setSelectedField(f.name)}
                />
              ))}
            </VStack>
          </Box>
        ) : (
          <Box>
            <SectionHeading>Link to a parent collection</SectionHeading>
            <VStack spacing={3} align="stretch">
              <Box>
                <Text fontSize="xs" color="gray.600" mb={1}>
                  Parent collection
                </Text>
                <Select
                  value={parentCollection}
                  onChange={(v) => setParentCollection(v as string)}
                  options={[
                    { value: "orders", label: "orders" },
                    { value: "payments", label: "payments" },
                    { value: "shipments", label: "shipments" },
                  ]}
                  style={{ width: "100%" }}
                />
              </Box>
              <Box>
                <Text fontSize="xs" color="gray.600" mb={1}>
                  FK column on this collection
                </Text>
                <Select
                  value={parentFkField}
                  onChange={(v) => setParentFkField(v as string)}
                  options={candidates.map((f) => ({
                    value: f.name,
                    label: `${f.name} (${f.type})`,
                  }))}
                  style={{ width: "100%" }}
                />
              </Box>
            </VStack>
          </Box>
        )}

        {applied && (
          <Box
            p={3}
            borderRadius="sm"
            bg="green.50"
            borderLeft="3px solid"
            borderColor="green.500"
            data-testid="wiring-confirmation"
          >
            <HStack spacing={2} mb={1}>
              <Icons.CheckmarkFilled color="var(--chakra-colors-green-500)" />
              <Text fontSize="sm" fontWeight="700" color="green.800">
                Reachability re-evaluated
              </Text>
            </HStack>
            <Text fontSize="sm" color="green.700">
              {mode === "identity"
                ? `Identity declared on ${collection.name}.${selectedField}. Collection is now Healthy.`
                : `FK link declared from ${collection.name}.${parentFkField} → ${parentCollection}. Collection is now Healthy.`}
            </Text>
          </Box>
        )}
      </VStack>
    </Drawer>
  );
};
