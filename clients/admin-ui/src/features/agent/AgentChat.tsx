/**
 * Main chat interface component for the AI Privacy Analyst Agent.
 */

import {
  ChakraBox as Box,
  ChakraButton as Button,
  ChakraFlex as Flex,
  ChakraHeading as Heading,
  ChakraSpinner as Spinner,
  ChakraText as Text,
  useChakraToast as useToast,
  ChakraVStack as VStack,
} from "fidesui";
import { useCallback, useEffect, useRef } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";

import {
  resetStreamingState,
  selectCurrentConversationId,
  selectIsStreaming,
  selectStreamingContent,
  selectStreamingError,
  selectStreamingToolCalls,
  setCurrentConversation,
  useCreateConversationMutation,
  useGetConversationQuery,
} from "./agent.slice";
import AgentChatInput from "./AgentChatInput";
import AgentChatMessage from "./AgentChatMessage";
import AgentConversationList from "./AgentConversationList";
import AgentWelcome from "./AgentWelcome";
import { useStreamingMessage } from "./hooks";
import type { Message } from "./types";

export default function AgentChat() {
  const dispatch = useAppDispatch();
  const toast = useToast();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const currentConversationId = useAppSelector(selectCurrentConversationId);
  const isStreaming = useAppSelector(selectIsStreaming);
  const streamingContent = useAppSelector(selectStreamingContent);
  const streamingToolCalls = useAppSelector(selectStreamingToolCalls);
  const streamingError = useAppSelector(selectStreamingError);

  const { sendMessage, cancelStream } = useStreamingMessage();
  const [createConversation] = useCreateConversationMutation();

  // Fetch current conversation with messages
  const {
    data: conversation,
    isLoading: isLoadingConversation,
    refetch: refetchConversation,
  } = useGetConversationQuery(currentConversationId!, {
    skip: !currentConversationId,
  });

  // Scroll to bottom when new content arrives
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation?.messages, streamingContent]);

  // Show error toast
  useEffect(() => {
    if (streamingError) {
      toast({
        title: "Error",
        description: streamingError,
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  }, [streamingError, toast]);

  // Refetch conversation after streaming completes
  useEffect(() => {
    if (!isStreaming && currentConversationId) {
      refetchConversation();
      dispatch(resetStreamingState());
    }
  }, [isStreaming, currentConversationId, refetchConversation, dispatch]);

  const handleSendMessage = useCallback(
    async (content: string) => {
      let conversationId = currentConversationId;

      // Create a new conversation if none exists
      if (!conversationId) {
        try {
          const result = await createConversation({}).unwrap();
          conversationId = result.id;
          dispatch(setCurrentConversation(conversationId));
        } catch (error) {
          toast({
            title: "Error creating conversation",
            description: String(error),
            status: "error",
            duration: 5000,
            isClosable: true,
          });
          return;
        }
      }

      // Send the message
      await sendMessage(conversationId, content);
    },
    [currentConversationId, createConversation, dispatch, sendMessage, toast]
  );

  const handleNewConversation = useCallback(() => {
    dispatch(setCurrentConversation(null));
    dispatch(resetStreamingState());
  }, [dispatch]);

  const handleSelectConversation = useCallback(
    (id: string) => {
      if (isStreaming) {
        cancelStream();
      }
      dispatch(setCurrentConversation(id));
      dispatch(resetStreamingState());
    },
    [dispatch, isStreaming, cancelStream]
  );

  // Build messages array including streaming content
  const displayMessages: Array<Message | { role: "assistant"; content: string; isStreaming: true }> = [
    ...(conversation?.messages || []),
  ];

  // Add streaming message if active
  if (isStreaming && streamingContent) {
    displayMessages.push({
      role: "assistant",
      content: streamingContent,
      isStreaming: true,
    } as Message & { isStreaming: true });
  }

  return (
    <Flex h="calc(100vh - 56px)" overflow="hidden">
      {/* Conversation sidebar */}
      <Box
        w="280px"
        borderRight="1px solid"
        borderColor="gray.200"
        bg="gray.50"
        overflow="hidden"
        display="flex"
        flexDirection="column"
      >
        <Box p={4} borderBottom="1px solid" borderColor="gray.200">
          <Button
            colorScheme="primary"
            variant="outline"
            size="sm"
            w="100%"
            onClick={handleNewConversation}
            isDisabled={isStreaming}
          >
            New Conversation
          </Button>
        </Box>
        <Box flex={1} overflow="auto">
          <AgentConversationList
            selectedId={currentConversationId}
            onSelect={handleSelectConversation}
          />
        </Box>
      </Box>

      {/* Main chat area */}
      <Flex flex={1} direction="column" overflow="hidden">
        {/* Header */}
        <Box p={4} borderBottom="1px solid" borderColor="gray.200" bg="white">
          <Heading size="md">
            {conversation?.title || "Privacy Analyst Assistant"}
          </Heading>
          {conversation && (
            <Text fontSize="sm" color="gray.500">
              {conversation.messages.length} messages
            </Text>
          )}
        </Box>

        {/* Messages */}
        <Box flex={1} overflow="auto" p={4} bg="gray.50">
          {!currentConversationId ? (
            <AgentWelcome onExampleClick={handleSendMessage} />
          ) : isLoadingConversation ? (
            <Flex justify="center" align="center" h="100%">
              <Spinner size="lg" />
            </Flex>
          ) : (
            <VStack spacing={4} align="stretch">
              {displayMessages.map((message, index) => (
                <AgentChatMessage
                  key={
                    "id" in message
                      ? message.id
                      : `streaming-${index}`
                  }
                  message={message}
                  isStreaming={"isStreaming" in message && message.isStreaming}
                  toolCalls={
                    "isStreaming" in message && message.isStreaming
                      ? streamingToolCalls
                      : undefined
                  }
                />
              ))}
              <div ref={messagesEndRef} />
            </VStack>
          )}
        </Box>

        {/* Input */}
        <Box p={4} borderTop="1px solid" borderColor="gray.200" bg="white">
          <AgentChatInput
            onSend={handleSendMessage}
            isDisabled={isStreaming}
            onCancel={isStreaming ? cancelStream : undefined}
          />
        </Box>
      </Flex>
    </Flex>
  );
}
