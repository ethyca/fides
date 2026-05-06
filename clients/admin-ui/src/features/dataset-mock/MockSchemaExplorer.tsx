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
  SparkleIcon,
  Switch,
  Tag,
  Title,
  Tree,
} from "fidesui";
import { useMemo, useState } from "react";

import { IdentityWiringDrawer } from "./IdentityWiringDrawer";
import {
  FieldStatus,
  MOCK_COLLECTION_DETAILS,
  MOCK_DATASET_TREE,
  MockField,
  MockTreeNode,
} from "./mock-tree-data";

const fieldStatusColor = (s: FieldStatus): CUSTOM_TAG_COLOR => {
  if (s === "approved") {
    return CUSTOM_TAG_COLOR.SUCCESS;
  }
  if (s === "classified") {
    return CUSTOM_TAG_COLOR.INFO;
  }
  return CUSTOM_TAG_COLOR.DEFAULT;
};

const fieldStatusLabel = (s: FieldStatus): string => {
  if (s === "approved") {
    return "Approved";
  }
  if (s === "classified") {
    return "Classified";
  }
  return "Unlabeled";
};

const collectionStatusBadge = (status: MockTreeNode["status"]) => {
  if (status === "needs-dsr-wiring") {
    return <Tag color={CUSTOM_TAG_COLOR.ERROR}>Needs DSR wiring</Tag>;
  }
  if (status === "skipped") {
    return <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>Skipped</Tag>;
  }
  return null;
};

const treeNodeIcon = (node: MockTreeNode) => {
  if (node.type === "dataset") {
    return <Icons.Layers size={14} />;
  }
  if (node.status === "needs-dsr-wiring") {
    return <Icons.WarningAlt size={14} />;
  }
  if (node.status === "skipped") {
    return <Icons.ViewOff size={14} />;
  }
  return <Icons.DataTable size={14} />;
};

const buildTreeData = (root: MockTreeNode): any[] => {
  const renderTitle = (node: MockTreeNode) => {
    return (
      <HStack spacing={1.5}>
        <span>{node.title}</span>
        {collectionStatusBadge(node.status)}
      </HStack>
    );
  };
  const map = (n: MockTreeNode): any => ({
    key: n.key,
    title: renderTitle(n),
    icon: treeNodeIcon(n),
    isLeaf: n.type === "collection",
    children: n.children?.map(map),
  });
  return [map(root)];
};

const ConfidenceBar = ({ value }: { value: number }) => {
  const pct = Math.round(value * 100);
  const color = value >= 0.9 ? "green.500" : value >= 0.7 ? "yellow.500" : "gray.400";
  return (
    <HStack spacing={2} minW="90px">
      <Box w="48px" h="6px" bg="gray.100" borderRadius="full" overflow="hidden">
        <Box w={`${pct}%`} h="100%" bg={color} />
      </Box>
      <Text fontSize="xs" color="gray.600">
        {value > 0 ? `${pct}%` : "—"}
      </Text>
    </HStack>
  );
};

const FieldRow = ({ field, last }: { field: MockField; last: boolean }) => (
  <Box
    py={3}
    px={4}
    borderBottom={last ? "none" : "1px solid"}
    borderColor="gray.100"
    data-testid={`field-${field.name}`}
  >
    <Flex align="center" gap={4}>
      <Box minW="220px">
        <HStack spacing={2}>
          <Text fontWeight="600" fontSize="sm">
            {field.name}
          </Text>
          {field.isIdentity && (
            <Tag color={CUSTOM_TAG_COLOR.MINOS}>Identity</Tag>
          )}
          {field.isIdentityCandidate && (
            <Tag color={CUSTOM_TAG_COLOR.NECTAR}>
              <HStack spacing={1}>
                <SparkleIcon size={10} />
                <span>Identity candidate</span>
              </HStack>
            </Tag>
          )}
        </HStack>
        <Text fontSize="xs" color="gray.500" fontFamily="mono">
          {field.type}
        </Text>
      </Box>

      <Box minW="120px">
        <Tag color={fieldStatusColor(field.status)}>
          {fieldStatusLabel(field.status)}
        </Tag>
      </Box>

      <HStack spacing={1} flexWrap="wrap" flex={1}>
        {field.dataCategories.length === 0 && (
          <Text fontSize="xs" color="gray.400">
            —
          </Text>
        )}
        {field.dataCategories.map((c) => (
          <Tag key={c} color={CUSTOM_TAG_COLOR.MARBLE}>
            {c}
          </Tag>
        ))}
      </HStack>

      <Box minW="160px">
        {field.fkRef ? (
          <HStack spacing={1}>
            <Icons.Link size={12} color="var(--chakra-colors-gray-500)" />
            <Text fontSize="xs" color="gray.600" fontFamily="mono">
              FK → {field.fkRef}
            </Text>
          </HStack>
        ) : (
          <Text fontSize="xs" color="gray.300">
            —
          </Text>
        )}
      </Box>

      <ConfidenceBar value={field.confidence} />
    </Flex>
  </Box>
);

interface MockSchemaExplorerProps {
  collectionKey: string; // e.g. "users"
  initialWireDrawerOpen?: boolean;
}

export const MockSchemaExplorer = ({
  collectionKey,
  initialWireDrawerOpen = false,
}: MockSchemaExplorerProps) => {
  const [showAll, setShowAll] = useState(false);
  const [selectedKey, setSelectedKey] = useState<string>(
    `legacy_orders_pg.${collectionKey}`,
  );
  const [wireDrawerOpen, setWireDrawerOpen] = useState<boolean>(
    initialWireDrawerOpen,
  );

  const treeData = useMemo(() => buildTreeData(MOCK_DATASET_TREE), []);

  const activeCollectionName = selectedKey.split(".").slice(1).join(".");
  const detail =
    MOCK_COLLECTION_DETAILS[activeCollectionName] ??
    MOCK_COLLECTION_DETAILS.users;

  const visibleFields = useMemo(
    () =>
      showAll
        ? detail.fields
        : detail.fields.filter((f) => f.status === "approved"),
    [detail, showAll],
  );

  return (
    <Flex
      gap={4}
      align="stretch"
      data-testid="mock-schema-explorer"
      h="calc(100vh - 220px)"
      minH="600px"
    >
      <Box
        w="320px"
        flexShrink={0}
        bg="white"
        border="1px solid"
        borderColor="gray.200"
        borderRadius="md"
        p={4}
        overflowY="auto"
      >
        <Title level={3} style={{ fontSize: "0.95rem", marginBottom: 12 }}>
          Schema explorer
        </Title>
        <Tree.DirectoryTree
          showIcon
          defaultExpandAll
          selectedKeys={[selectedKey]}
          onSelect={(keys) => {
            if (keys[0]) {
              setSelectedKey(String(keys[0]));
            }
          }}
          treeData={treeData}
        />
      </Box>

      <Box
        flex={1}
        bg="white"
        border="1px solid"
        borderColor="gray.200"
        borderRadius="md"
        overflow="hidden"
        display="flex"
        flexDirection="column"
      >
        <Box p={4} borderBottom="1px solid" borderColor="gray.200">
          <Flex align="center" justify="space-between" mb={2} gap={4}>
            <HStack spacing={2}>
              <Icons.DataTable size={18} />
              <Text fontSize="lg" fontWeight="700">
                {detail.name}
              </Text>
              {collectionStatusBadge(detail.status)}
            </HStack>
            <HStack spacing={3}>
              <HStack spacing={2}>
                <Text fontSize="sm" color="gray.600">
                  Show all discovered fields
                </Text>
                <Switch checked={showAll} onChange={(v) => setShowAll(v)} />
              </HStack>
              {detail.status === "needs-dsr-wiring" && (
                <Button
                  type="primary"
                  icon={<Icons.Settings />}
                  onClick={() => setWireDrawerOpen(true)}
                  data-testid="wire-dsr-btn"
                >
                  Wire DSR
                </Button>
              )}
            </HStack>
          </Flex>
          {detail.reason && (
            <HStack
              spacing={2}
              p={2}
              bg="red.50"
              borderRadius="sm"
              borderLeft="3px solid"
              borderColor="red.400"
            >
              <Icons.WarningAlt color="var(--chakra-colors-red-500)" />
              <Text fontSize="sm" color="red.700">
                {detail.reason}
              </Text>
            </HStack>
          )}
        </Box>

        <Box overflowY="auto" flex={1}>
          <Box
            px={4}
            py={2}
            bg="gray.50"
            borderBottom="1px solid"
            borderColor="gray.200"
          >
            <Flex gap={4} fontSize="xs" color="gray.600" fontWeight="600" textTransform="uppercase">
              <Box minW="220px">Field</Box>
              <Box minW="120px">Status</Box>
              <Box flex={1}>Data categories</Box>
              <Box minW="160px">FK ref</Box>
              <Box minW="90px">Confidence</Box>
            </Flex>
          </Box>
          {visibleFields.map((f, i) => (
            <FieldRow
              key={f.name}
              field={f}
              last={i === visibleFields.length - 1}
            />
          ))}
          {visibleFields.length === 0 && (
            <VStack py={10}>
              <Text fontSize="sm" color="gray.500">
                No approved fields. Toggle "Show all discovered fields" to see
                the rest.
              </Text>
            </VStack>
          )}
        </Box>

        <Box
          px={4}
          py={2}
          bg="gray.50"
          borderTop="1px solid"
          borderColor="gray.200"
        >
          <Text fontSize="xs" color="gray.600">
            Showing {visibleFields.length} of {detail.fields.length} fields
            {showAll
              ? " (including unlabeled)"
              : " — approved only. Toggle to show unlabeled fields."}
          </Text>
        </Box>
      </Box>

      <IdentityWiringDrawer
        open={wireDrawerOpen}
        onClose={() => setWireDrawerOpen(false)}
        collectionKey={activeCollectionName}
      />
    </Flex>
  );
};
