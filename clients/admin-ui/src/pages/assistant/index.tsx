import { ChakraBox as Box, ChakraFlex as Flex, Text } from "fidesui";
import type { NextPage } from "next";

import { useFeatures } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import { AgentChat } from "~/features/agent";

const AssistantPage: NextPage = () => {
  const { plus: hasPlus } = useFeatures();

  if (!hasPlus) {
    return (
      <Layout title="Assistant">
        <Flex
          direction="column"
          align="center"
          justify="center"
          h="100%"
          p={8}
        >
          <Box textAlign="center" maxW="500px">
            <Text fontSize="xl" fontWeight="bold" mb={4}>
              Privacy Analyst Assistant
            </Text>
            <Text color="gray.600" mb={6}>
              The AI-powered Privacy Analyst Assistant is available exclusively
              for Fides Plus users. Upgrade to access intelligent conversational
              analysis of your data map, privacy posture, and compliance status.
            </Text>
            <Text fontSize="sm" color="gray.500">
              Contact your account representative to learn more about Fides
              Plus.
            </Text>
          </Box>
        </Flex>
      </Layout>
    );
  }

  return (
    <Layout title="Assistant" padded={false}>
      <AgentChat />
    </Layout>
  );
};

export default AssistantPage;
