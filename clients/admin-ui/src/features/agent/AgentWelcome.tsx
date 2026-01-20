/**
 * Welcome screen component for new conversations with example prompts.
 */

import {
  ChakraBox as Box,
  ChakraButton as Button,
  ChakraFlex as Flex,
  ChakraHeading as Heading,
  ChakraSimpleGrid as SimpleGrid,
  ChakraText as Text,
  ChakraVStack as VStack,
} from "fidesui";

interface AgentWelcomeProps {
  onExampleClick: (content: string) => void;
}

const EXAMPLE_PROMPTS = [
  {
    title: "Data Map Overview",
    description: "Get a summary of your data map",
    prompt: "Give me an overview of our data map, including the number of systems, datasets, and data categories we're tracking.",
  },
  {
    title: "Compliance Status",
    description: "Check compliance across frameworks",
    prompt: "What is our current compliance posture? Are there any systems or data processing activities that may have compliance gaps?",
  },
  {
    title: "Sensitive Data",
    description: "Find systems with sensitive data",
    prompt: "Which systems process sensitive personal data like health information, financial data, or biometric data?",
  },
  {
    title: "Data Flows",
    description: "Understand data movement",
    prompt: "Can you trace the data flows for our customer data? Show me which systems receive customer information and where it goes.",
  },
  {
    title: "Third-Party Sharing",
    description: "Review external data sharing",
    prompt: "What third-party systems or vendors do we share personal data with? What categories of data are being shared?",
  },
  {
    title: "Recent Changes",
    description: "Review discovered resources",
    prompt: "Are there any newly discovered resources or staged systems that need to be reviewed and classified?",
  },
];

export default function AgentWelcome({ onExampleClick }: AgentWelcomeProps) {
  return (
    <Flex
      direction="column"
      align="center"
      justify="center"
      minH="100%"
      p={8}
    >
      <VStack spacing={6} maxW="800px" w="100%">
        <Box textAlign="center">
          <Heading size="lg" mb={2}>
            Privacy Analyst Assistant
          </Heading>
          <Text color="gray.600" fontSize="md">
            Ask questions about your data map, privacy posture, and compliance
            status. I can help you understand your data flows, identify risks,
            and navigate your privacy program.
          </Text>
        </Box>

        <Box w="100%" pt={4}>
          <Text fontWeight="medium" mb={3} color="gray.700">
            Try asking about:
          </Text>
          <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={3}>
            {EXAMPLE_PROMPTS.map((example) => (
              <Button
                key={example.title}
                variant="outline"
                h="auto"
                p={4}
                display="flex"
                flexDirection="column"
                alignItems="flex-start"
                textAlign="left"
                whiteSpace="normal"
                onClick={() => onExampleClick(example.prompt)}
                _hover={{
                  bg: "primary.50",
                  borderColor: "primary.300",
                }}
              >
                <Text fontWeight="semibold" fontSize="sm" mb={1}>
                  {example.title}
                </Text>
                <Text
                  fontSize="xs"
                  color="gray.500"
                  fontWeight="normal"
                >
                  {example.description}
                </Text>
              </Button>
            ))}
          </SimpleGrid>
        </Box>

        <Box
          mt={4}
          p={4}
          bg="blue.50"
          borderRadius="md"
          borderWidth="1px"
          borderColor="blue.100"
          w="100%"
        >
          <Text fontSize="sm" color="blue.800">
            <strong>Tip:</strong> The assistant has access to your complete data
            map including systems, datasets, privacy declarations, notices, and
            integrations. You can ask specific questions about any entity or
            request analysis across your entire privacy program.
          </Text>
        </Box>
      </VStack>
    </Flex>
  );
}
