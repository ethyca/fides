/**
 * Sidebar component for listing and selecting conversations.
 */

import {
  ChakraBox as Box,
  ChakraDeleteIcon as DeleteIcon,
  ChakraFlex as Flex,
  ChakraIconButton as IconButton,
  ChakraSpinner as Spinner,
  ChakraText as Text,
  ChakraVStack as VStack,
} from "fidesui";
import { useCallback, useState } from "react";

import {
  useDeleteConversationMutation,
  useListConversationsQuery,
} from "./agent.slice";

interface AgentConversationListProps {
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export default function AgentConversationList({
  selectedId,
  onSelect,
}: AgentConversationListProps) {
  const { data, isLoading, error } = useListConversationsQuery({
    page: 1,
    size: 50,
    include_archived: false,
  });

  const [deleteConversation] = useDeleteConversationMutation();
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = useCallback(
    async (e: React.MouseEvent, id: string) => {
      e.stopPropagation();
      setDeletingId(id);
      try {
        await deleteConversation(id).unwrap();
      } catch (err) {
        console.error("Failed to delete conversation:", err);
      } finally {
        setDeletingId(null);
      }
    },
    [deleteConversation]
  );

  if (isLoading) {
    return (
      <Flex justify="center" align="center" p={4}>
        <Spinner size="sm" />
      </Flex>
    );
  }

  if (error) {
    return (
      <Box p={4}>
        <Text color="red.500" fontSize="sm">
          Failed to load conversations
        </Text>
      </Box>
    );
  }

  if (!data?.items.length) {
    return (
      <Box p={4}>
        <Text color="gray.500" fontSize="sm" textAlign="center">
          No conversations yet
        </Text>
      </Box>
    );
  }

  return (
    <VStack spacing={0} align="stretch">
      {data.items.map((conversation) => (
        <Flex
          key={conversation.id}
          align="center"
          p={3}
          cursor="pointer"
          bg={selectedId === conversation.id ? "primary.50" : "transparent"}
          borderLeft="3px solid"
          borderColor={
            selectedId === conversation.id ? "primary.500" : "transparent"
          }
          _hover={{
            bg: selectedId === conversation.id ? "primary.50" : "gray.100",
          }}
          onClick={() => onSelect(conversation.id)}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              onSelect(conversation.id);
            }
          }}
        >
          <Box flex={1} minW={0}>
            <Text
              fontSize="sm"
              fontWeight={selectedId === conversation.id ? "medium" : "normal"}
              noOfLines={1}
            >
              {conversation.title || "New Conversation"}
            </Text>
            <Text fontSize="xs" color="gray.500">
              {formatRelativeTime(conversation.updated_at)}
            </Text>
          </Box>
          <IconButton
            aria-label="Delete conversation"
            icon={
              deletingId === conversation.id ? (
                <Spinner size="xs" />
              ) : (
                <DeleteIcon />
              )
            }
            size="xs"
            variant="ghost"
            colorScheme="red"
            opacity={0}
            _groupHover={{ opacity: 1 }}
            sx={{
              ".chakra-flex:hover &": { opacity: 1 },
            }}
            onClick={(e) => handleDelete(e, conversation.id)}
            isDisabled={deletingId === conversation.id}
          />
        </Flex>
      ))}
    </VStack>
  );
}

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffMins < 1) {
    return "Just now";
  }
  if (diffMins < 60) {
    return `${diffMins}m ago`;
  }
  if (diffHours < 24) {
    return `${diffHours}h ago`;
  }
  if (diffDays < 7) {
    return `${diffDays}d ago`;
  }
  return date.toLocaleDateString();
}
