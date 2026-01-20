import {
  Bubble,
  Conversations,
  ConversationsProps,
  Prompts,
  Sender,
  Welcome,
} from "@ant-design/x";
import { Alert, Button, Flex, Icons } from "fidesui";
import React, { useState } from "react";

import { useAskPrivacyExpertMutation } from "~/features/plus/plus.slice";

const MAX_MESSAGES = 40;

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

interface Conversation {
  id: string;
  title: string;
  messages: Message[];
}

const EXAMPLE_PROMPTS = [
  {
    key: "1",
    description: "What data categories does GDPR regulate?",
  },
  {
    key: "2",
    description: "How should I handle user consent for marketing emails?",
  },
  {
    key: "3",
    description: "What are the key differences between GDPR and CCPA?",
  },
];

const PrivacyConsultantChat = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<
    string | null
  >(null);

  const [askPrivacyExpert, { isLoading }] = useAskPrivacyExpertMutation();

  const activeConversation = conversations.find(
    (c) => c.id === activeConversationId,
  );
  const messages = activeConversation?.messages ?? [];
  const isAtLimit = messages.length >= MAX_MESSAGES;

  const createNewConversation = () => {
    const newId = crypto.randomUUID();
    const newConversation: Conversation = {
      id: newId,
      title: `Conversation ${conversations.length + 1}`,
      messages: [],
    };
    setConversations((prev) => [...prev, newConversation]);
    setActiveConversationId(newId);
  };

  const handleSend = async (content: string) => {
    if (!content.trim() || isAtLimit) {
      return;
    }

    // Create a new conversation if none exists
    let currentConversationId = activeConversationId;
    if (!currentConversationId) {
      const newId = crypto.randomUUID();
      const newConversation: Conversation = {
        id: newId,
        title: content.slice(0, 30) + (content.length > 30 ? "..." : ""),
        messages: [],
      };
      setConversations((prev) => [...prev, newConversation]);
      setActiveConversationId(newId);
      currentConversationId = newId;
    }

    // Add user message
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content,
    };

    setConversations((prev) =>
      prev.map((c) =>
        c.id === currentConversationId
          ? { ...c, messages: [...c.messages, userMessage] }
          : c,
      ),
    );

    try {
      const response = await askPrivacyExpert({ question: content }).unwrap();

      // Add assistant message
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.answer,
      };

      setConversations((prev) =>
        prev.map((c) =>
          c.id === currentConversationId
            ? { ...c, messages: [...c.messages, assistantMessage] }
            : c,
        ),
      );
    } catch {
      // Add error message
      const errorMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "Sorry, there was an error processing your request.",
      };

      setConversations((prev) =>
        prev.map((c) =>
          c.id === currentConversationId
            ? { ...c, messages: [...c.messages, errorMessage] }
            : c,
        ),
      );
    }
  };

  const handlePromptClick = (info: {
    data: { key?: string; description?: React.ReactNode };
  }) => {
    if (typeof info.data.description === "string") {
      handleSend(info.data.description);
    }
  };

  const conversationItems: ConversationsProps["items"] = conversations.map(
    (c) => ({
      key: c.id,
      label: c.title,
    }),
  );

  const handleConversationChange = (key: string) => {
    setActiveConversationId(key);
  };

  const bubbleItems = messages.map((msg) => ({
    key: msg.id,
    content: msg.content,
    placement: msg.role === "user" ? ("end" as const) : ("start" as const),
    role: msg.role,
  }));

  return (
    <Flex className="h-full">
      {/* Left sidebar */}
      <Flex vertical className="w-64">
        <Button
          type="primary"
          onClick={createNewConversation}
          data-testid="new-chat-btn"
          icon={<Icons.Add />}
        >
          New chat
        </Button>
        <Conversations
          items={conversationItems}
          activeKey={activeConversationId ?? undefined}
          onActiveChange={handleConversationChange}
        />
      </Flex>

      {/* Right chat area */}
      <Flex vertical flex={1}>
        {/* Message area */}
        <Flex vertical flex={1} className="overflow-y-auto">
          {messages.length === 0 ? (
            <Flex vertical align="center" justify="center" flex={1}>
              <Welcome
                title="Privacy consultant"
                description="Ask questions about privacy regulations, compliance, and best practices."
              />
              <Prompts
                items={EXAMPLE_PROMPTS}
                onItemClick={handlePromptClick}
              />
            </Flex>
          ) : (
            <Bubble.List items={bubbleItems} autoScroll />
          )}
        </Flex>

        {/* Message limit alert */}
        {isAtLimit && (
          <Alert
            message="Message limit reached. Please start a new conversation."
            type="warning"
            showIcon
          />
        )}

        {/* Input area */}
        <Sender
          loading={isLoading}
          disabled={isAtLimit}
          onSubmit={handleSend}
          placeholder={
            isAtLimit ? "Message limit reached" : "Ask your privacy question..."
          }
          data-testid="chat-sender"
        />
      </Flex>
    </Flex>
  );
};

export default PrivacyConsultantChat;
