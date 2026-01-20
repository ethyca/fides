import {
  ChakraBox as Box,
  ChakraFlex as Flex,
  ChakraHeading as Heading,
  ChakraSpinner as Spinner,
  ChakraText as Text,
  ChakraVStack as VStack,
  Button,
  useChakraToast as useToast,
} from "fidesui";
import type { NextPage } from "next";

import { useFeatures } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import {
  useGetAgentSettingsQuery,
  useGetEmbeddingStatusQuery,
  useSyncEmbeddingsMutation,
} from "~/features/agent";

const AssistantSettingsPage: NextPage = () => {
  const { plus: hasPlus } = useFeatures();
  const toast = useToast();

  const { data: settings, isLoading: isLoadingSettings } =
    useGetAgentSettingsQuery(undefined, { skip: !hasPlus });
  const { data: embeddingStatus, isLoading: isLoadingStatus } =
    useGetEmbeddingStatusQuery(undefined, { skip: !hasPlus });
  const [syncEmbeddings, { isLoading: isSyncing }] =
    useSyncEmbeddingsMutation();

  const handleSync = async () => {
    try {
      const result = await syncEmbeddings({}).unwrap();
      toast({
        title: "Embedding sync started",
        description: `Processing ${result.entities_queued} entities`,
        status: "success",
        duration: 5000,
        isClosable: true,
      });
    } catch (error) {
      toast({
        title: "Sync failed",
        description: String(error),
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  if (!hasPlus) {
    return (
      <Layout title="Assistant Settings">
        <Box data-testid="assistant-settings">
          <PageHeader heading="Assistant Settings" />
          <Text color="gray.600">
            The AI-powered Privacy Analyst Assistant is available exclusively
            for Fides Plus users.
          </Text>
        </Box>
      </Layout>
    );
  }

  if (isLoadingSettings || isLoadingStatus) {
    return (
      <Layout title="Assistant Settings">
        <Box data-testid="assistant-settings">
          <PageHeader heading="Assistant Settings" />
          <Flex justify="center" align="center" h="200px">
            <Spinner size="lg" />
          </Flex>
        </Box>
      </Layout>
    );
  }

  return (
    <Layout title="Assistant Settings">
      <Box data-testid="assistant-settings">
        <PageHeader heading="Assistant Settings" />
        <Box maxWidth="800px">
          <Text pb={6} fontSize="sm" color="gray.600">
            Configure your AI Privacy Analyst Assistant settings and manage the
            knowledge index.
          </Text>

          <VStack spacing={6} align="stretch">
            {/* Organization Context */}
            <Box background="gray.50" p={4} borderRadius="md">
              <Heading size="sm" mb={3}>
                Organization Context
              </Heading>
              <Text fontSize="sm" color="gray.600" mb={2}>
                The assistant uses your organization details to provide
                contextual responses.
              </Text>
              {settings?.organization_name && (
                <Text fontSize="sm">
                  <strong>Organization:</strong> {settings.organization_name}
                </Text>
              )}
              <Text fontSize="xs" color="gray.500" mt={2}>
                Update organization details in{" "}
                <a
                  href="/settings/organization"
                  style={{ textDecoration: "underline" }}
                >
                  Organization Settings
                </a>
              </Text>
            </Box>

            {/* Compliance Frameworks */}
            <Box background="gray.50" p={4} borderRadius="md">
              <Heading size="sm" mb={3}>
                Compliance Frameworks
              </Heading>
              <Text fontSize="sm" color="gray.600" mb={2}>
                The assistant will consider these frameworks when providing
                compliance guidance.
              </Text>
              {settings?.compliance_frameworks &&
              settings.compliance_frameworks.length > 0 ? (
                <Flex gap={2} flexWrap="wrap">
                  {settings.compliance_frameworks.map((framework) => (
                    <Box
                      key={framework}
                      bg="primary.100"
                      color="primary.800"
                      px={2}
                      py={1}
                      borderRadius="md"
                      fontSize="sm"
                    >
                      {framework}
                    </Box>
                  ))}
                </Flex>
              ) : (
                <Text fontSize="sm" color="gray.500">
                  No compliance frameworks configured
                </Text>
              )}
            </Box>

            {/* Embedding Index Status */}
            <Box background="gray.50" p={4} borderRadius="md">
              <Flex justify="space-between" align="center" mb={3}>
                <Heading size="sm">Knowledge Index</Heading>
                <Button
                  size="sm"
                  colorScheme="primary"
                  onClick={handleSync}
                  isLoading={isSyncing}
                  loadingText="Syncing..."
                >
                  Rebuild Index
                </Button>
              </Flex>
              <Text fontSize="sm" color="gray.600" mb={3}>
                The knowledge index enables semantic search across your data
                map. Rebuild it after significant changes.
              </Text>
              {embeddingStatus && (
                <Box fontSize="sm">
                  <Flex justify="space-between" py={1}>
                    <Text color="gray.600">Total Entities Indexed:</Text>
                    <Text fontWeight="medium">
                      {embeddingStatus.total_embeddings}
                    </Text>
                  </Flex>
                  <Flex justify="space-between" py={1}>
                    <Text color="gray.600">Pending Updates:</Text>
                    <Text fontWeight="medium">
                      {embeddingStatus.pending_updates}
                    </Text>
                  </Flex>
                  {embeddingStatus.last_sync && (
                    <Flex justify="space-between" py={1}>
                      <Text color="gray.600">Last Sync:</Text>
                      <Text fontWeight="medium">
                        {new Date(embeddingStatus.last_sync).toLocaleString()}
                      </Text>
                    </Flex>
                  )}
                  {embeddingStatus.entities_by_type && (
                    <Box mt={3}>
                      <Text color="gray.600" mb={2}>
                        Indexed by Type:
                      </Text>
                      <Flex gap={2} flexWrap="wrap">
                        {Object.entries(embeddingStatus.entities_by_type).map(
                          ([type, count]) => (
                            <Box
                              key={type}
                              bg="gray.100"
                              px={2}
                              py={1}
                              borderRadius="md"
                              fontSize="xs"
                            >
                              {type}: {count}
                            </Box>
                          )
                        )}
                      </Flex>
                    </Box>
                  )}
                </Box>
              )}
            </Box>
          </VStack>
        </Box>
      </Box>
    </Layout>
  );
};

export default AssistantSettingsPage;
