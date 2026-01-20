/**
 * Individual message display component with markdown rendering and tool call visualization.
 */

import {
  ChakraBox as Box,
  ChakraChevronDownIcon as ChevronDownIcon,
  ChakraChevronRightIcon as ChevronRightIcon,
  ChakraCode as Code,
  Collapse,
  ChakraFlex as Flex,
  ChakraIconButton as IconButton,
  ChakraSpinner as Spinner,
  ChakraText as Text,
  useChakraDisclosure as useDisclosure,
} from "fidesui";
import Link from "next/link";
import { useMemo } from "react";

import type { Message, ToolCall } from "./types";

interface AgentChatMessageProps {
  message: Message | { role: "assistant"; content: string; isStreaming: true };
  isStreaming?: boolean;
  toolCalls?: Array<{
    id: string;
    name: string;
    arguments: Record<string, unknown>;
    result?: string;
  }>;
}

// Entity link patterns for converting references to clickable links
const ENTITY_PATTERNS: Array<{
  pattern: RegExp;
  getPath: (match: RegExpMatchArray) => string;
}> = [
  {
    pattern: /\[System: ([^\]]+)\]\(([^)]+)\)/g,
    getPath: (match) => `/systems/configure/${encodeURIComponent(match[2])}`,
  },
  {
    pattern: /\[Dataset: ([^\]]+)\]\(([^)]+)\)/g,
    getPath: (match) => `/dataset/${encodeURIComponent(match[2])}`,
  },
  {
    pattern: /\[Connection: ([^\]]+)\]\(([^)]+)\)/g,
    getPath: (match) => `/integrations/${encodeURIComponent(match[2])}`,
  },
];

function ToolCallDisplay({
  toolCall,
}: {
  toolCall: ToolCall & { result?: string };
}) {
  const { isOpen, onToggle } = useDisclosure();
  const hasResult = toolCall.result !== undefined;

  return (
    <Box
      borderWidth="1px"
      borderColor="gray.200"
      borderRadius="md"
      mb={2}
      overflow="hidden"
    >
      <Flex
        align="center"
        p={2}
        bg="gray.50"
        cursor="pointer"
        onClick={onToggle}
        _hover={{ bg: "gray.100" }}
      >
        <IconButton
          aria-label="Toggle details"
          icon={isOpen ? <ChevronDownIcon /> : <ChevronRightIcon />}
          size="xs"
          variant="ghost"
          mr={2}
        />
        <Code fontSize="sm" bg="transparent" color="purple.600">
          {toolCall.name}
        </Code>
        {!hasResult && <Spinner size="xs" ml={2} />}
        {hasResult && (
          <Text fontSize="xs" color="green.600" ml={2}>
            Complete
          </Text>
        )}
      </Flex>
      <Collapse
        items={[
          {
            key: "1",
            label: "",
            children: (
              <Box p={3} bg="white" fontSize="sm">
                <Text fontWeight="medium" mb={1}>
                  Arguments:
                </Text>
                <Code
                  display="block"
                  whiteSpace="pre-wrap"
                  p={2}
                  bg="gray.50"
                  borderRadius="md"
                  fontSize="xs"
                  mb={hasResult ? 3 : 0}
                >
                  {JSON.stringify(toolCall.arguments, null, 2)}
                </Code>
                {hasResult && (
                  <>
                    <Text fontWeight="medium" mb={1}>
                      Result:
                    </Text>
                    <Code
                      display="block"
                      whiteSpace="pre-wrap"
                      p={2}
                      bg="gray.50"
                      borderRadius="md"
                      fontSize="xs"
                      maxH="200px"
                      overflow="auto"
                    >
                      {toolCall.result}
                    </Code>
                  </>
                )}
              </Box>
            ),
          },
        ]}
        activeKey={isOpen ? ["1"] : []}
        onChange={onToggle}
        bordered={false}
        ghost
      />
    </Box>
  );
}

function MarkdownContent({ content }: { content: string }) {
  // Process content to convert entity references to clickable links
  const processedContent = useMemo(() => {
    let result = content;
    ENTITY_PATTERNS.forEach(({ pattern }) => {
      result = result.replace(pattern, (match, name) => name);
    });
    return result;
  }, [content]);

  // Split content into paragraphs for basic formatting
  const paragraphs = processedContent.split("\n\n").filter((p) => p.trim());

  return (
    <Box>
      {paragraphs.map((paragraph, index) => (
        <Text
          key={index}
          mb={index < paragraphs.length - 1 ? 2 : 0}
          whiteSpace="pre-wrap"
        >
          {paragraph}
        </Text>
      ))}
    </Box>
  );
}

export default function AgentChatMessage({
  message,
  isStreaming,
  toolCalls,
}: AgentChatMessageProps) {
  const isUser = message.role === "user";
  const isAssistant = message.role === "assistant";

  // Get tool calls from message or streaming state
  const displayToolCalls =
    toolCalls ||
    ("tool_calls" in message && message.tool_calls
      ? message.tool_calls.map((tc) => ({
          id: tc.id,
          name: tc.name,
          arguments: tc.arguments,
          result: tc.result,
        }))
      : []);

  return (
    <Box
      bg={isUser ? "primary.50" : "white"}
      p={4}
      borderRadius="lg"
      borderWidth="1px"
      borderColor={isUser ? "primary.100" : "gray.200"}
      maxW={isUser ? "80%" : "100%"}
      ml={isUser ? "auto" : 0}
    >
      <Flex align="center" mb={2}>
        <Box
          w={6}
          h={6}
          borderRadius="full"
          bg={isUser ? "primary.500" : "purple.500"}
          display="flex"
          alignItems="center"
          justifyContent="center"
          mr={2}
        >
          <Text fontSize="xs" color="white" fontWeight="bold">
            {isUser ? "U" : "A"}
          </Text>
        </Box>
        <Text fontWeight="medium" fontSize="sm" color="gray.600">
          {isUser ? "You" : "Privacy Analyst"}
        </Text>
        {isStreaming && <Spinner size="xs" ml={2} />}
      </Flex>

      {/* Tool calls display */}
      {displayToolCalls.length > 0 && (
        <Box mb={3}>
          {displayToolCalls.map((tc) => (
            <ToolCallDisplay key={tc.id} toolCall={tc} />
          ))}
        </Box>
      )}

      {/* Message content */}
      {message.content && <MarkdownContent content={message.content} />}

      {/* Streaming cursor */}
      {isStreaming && (
        <Box
          as="span"
          display="inline-block"
          w="2px"
          h="1em"
          bg="gray.400"
          ml={1}
          animation="blink 1s infinite"
          sx={{
            "@keyframes blink": {
              "0%, 50%": { opacity: 1 },
              "51%, 100%": { opacity: 0 },
            },
          }}
        />
      )}
    </Box>
  );
}
