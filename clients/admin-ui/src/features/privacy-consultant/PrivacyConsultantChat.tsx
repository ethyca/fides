import {
  Alert,
  Button,
  Card,
  Flex,
  Icons,
  Input,
  Menu,
  Spin,
  Text,
  Title,
} from "fidesui";
import React, { useEffect, useMemo, useRef, useState } from "react";

import { useAskPrivacyExpertMutation } from "~/features/plus/plus.slice";

import { parseMarkdown } from "./parseMarkdown";
import styles from "./PrivacyConsultantChat.module.scss";

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

const CAPABILITIES = [
  {
    key: "consent",
    title: "Validate Consent",
    description:
      "Check if your opt-in flows meet legal requirements for the specific data being collected.",
    examplePrompt:
      "I'm adding a location-tracking feature to our mobile app for a new rewards program. Can you check our current Consent & Cookie configuration to see if our existing 'opt-in' banner covers this, or do I need to create a new one?",
  },
  {
    key: "systems",
    title: "Map Systems",
    description:
      "Identify where the data lives and who is responsible for it (The Data Map).",
    examplePrompt:
      "I need to share 'purchase history' and 'user profiles' with an external financial vendor for reward disbursement. Which of our internal data systems currently hold these labels, and who are the data stewards I need to notify?",
  },
  {
    key: "risk",
    title: "Assess Risk",
    description:
      "Determine if the project triggers a legal requirement like a Data Protection Impact Assessment (DPIA).",
    examplePrompt:
      "We are planning to link behavioral 'in-app activity' data to a new third-party payment processor. Based on our Fideslang data uses, does this new processing trigger a DPIA requirement, or is our current risk assessment sufficient?",
  },
];

const PrivacyConsultantChat = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<
    string | null
  >(null);
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [askPrivacyExpert, { isLoading }] = useAskPrivacyExpertMutation();

  const activeConversation = conversations.find(
    (c) => c.id === activeConversationId,
  );
  const messages = useMemo(
    () => activeConversation?.messages ?? [],
    [activeConversation?.messages],
  );
  const isAtLimit = messages.length >= MAX_MESSAGES;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages.length]);

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
    if (!content.trim() || isAtLimit || isLoading) {
      return;
    }

    // Capture existing messages before state updates for conversation history
    const existingMessages = activeConversation?.messages ?? [];

    setInputValue("");

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
      const response = await askPrivacyExpert({
        question: content,
        messages: existingMessages.map((msg) => ({
          role: msg.role,
          content: msg.content,
        })),
      }).unwrap();

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

  const handlePromptClick = (prompt: string) => {
    handleSend(prompt);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend(inputValue);
    }
  };

  const conversationMenuItems = conversations.map((c) => ({
    key: c.id,
    label: c.title,
    icon: <Icons.Chat size={16} />,
  }));

  return (
    <Flex className={styles.container}>
      {/* Left sidebar */}
      <Flex vertical className={styles.sidebar} gap={8}>
        <Button
          type="primary"
          onClick={createNewConversation}
          data-testid="new-chat-btn"
          icon={<Icons.Add size={16} />}
          block
        >
          New chat
        </Button>
        <Menu
          mode="inline"
          selectedKeys={activeConversationId ? [activeConversationId] : []}
          onClick={({ key }) => setActiveConversationId(key)}
          items={conversationMenuItems}
          className={styles.conversationMenu}
        />
      </Flex>

      {/* Right chat area */}
      <Flex vertical flex={1} className={styles.chatArea}>
        {/* Message area */}
        <Flex vertical flex={1} className={styles.messageArea}>
          {messages.length === 0 ? (
            <Flex
              vertical
              align="center"
              justify="center"
              flex={1}
              gap={32}
              className={styles.welcomeContainer}
            >
              <Flex vertical align="center" gap={16}>
                <Title level={2}>Welcome to Hermes</Title>
                <Text type="secondary" className={styles.welcomeText}>
                  I am integrated with Fides and synced with your current Data
                  Map and Privacy Center.
                </Text>
                <Text type="secondary" className={styles.welcomeText}>
                  Tell me about the new product or feature you are building. I
                  will help you:
                </Text>
              </Flex>
              <Flex gap={16} wrap="wrap" justify="center">
                {CAPABILITIES.map((capability) => (
                  <Card
                    key={capability.key}
                    hoverable
                    className={styles.capabilityCard}
                    onClick={() => handlePromptClick(capability.examplePrompt)}
                  >
                    <Flex vertical gap={8}>
                      <Title level={5}>{capability.title}</Title>
                      <Text type="secondary">{capability.description}</Text>
                      <Text className={styles.examplePrompt}>
                        {capability.examplePrompt}
                      </Text>
                    </Flex>
                  </Card>
                ))}
              </Flex>
            </Flex>
          ) : (
            <Flex vertical gap={16} className={styles.messageList}>
              {messages.map((msg) => (
                <Flex
                  key={msg.id}
                  justify={msg.role === "user" ? "flex-end" : "flex-start"}
                >
                  <div
                    className={
                      msg.role === "user"
                        ? styles.userMessage
                        : styles.assistantMessage
                    }
                  >
                    <Text>{parseMarkdown(msg.content)}</Text>
                  </div>
                </Flex>
              ))}
              {isLoading && (
                <Flex justify="flex-start">
                  <div className={styles.assistantMessage}>
                    <Spin size="small" />
                  </div>
                </Flex>
              )}
              <div ref={messagesEndRef} />
            </Flex>
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
        <Flex gap={8} className={styles.inputArea}>
          <Input.TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              isAtLimit
                ? "Message limit reached"
                : "Ask your privacy question..."
            }
            disabled={isAtLimit}
            autoSize={{ minRows: 1, maxRows: 4 }}
            data-testid="chat-input"
            className={styles.chatInput}
            aria-label="Chat message input"
          />
          <Button
            type="primary"
            onClick={() => handleSend(inputValue)}
            loading={isLoading}
            disabled={isAtLimit || !inputValue.trim()}
            icon={<Icons.Send size={16} />}
            data-testid="chat-send-btn"
            aria-label="Send message"
          />
        </Flex>
      </Flex>
    </Flex>
  );
};

export default PrivacyConsultantChat;
