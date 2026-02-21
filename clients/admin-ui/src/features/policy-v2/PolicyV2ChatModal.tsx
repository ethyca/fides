import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  Modal,
  Input,
  Button,
  Space,
  Typography,
  Spin,
  Flex,
  Divider,
  Select,
  Tooltip,
  Alert,
  useChakraToast as useToast,
} from "fidesui";
import Markdown from "react-markdown";

import modalStyles from "./PolicyV2ChatModal.module.scss";

import { errorToastParams, successToastParams } from "~/features/common/toast";

const { TextArea } = Input;
const { Text, Title, Paragraph } = Typography;

import {
  useSendPolicyV2ChatMutation,
  useClearPolicyV2ChatMutation,
} from "./policy-v2.slice";
import { PolicyV2Create } from "./types";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface PolicyV2ChatModalProps {
  isOpen: boolean;
  onClose: () => void;
  onPolicyGenerated: (policy: PolicyV2Create) => void;
}

const AI_MODELS = [
  { value: "gemini/gemini-2.5-flash", label: "Gemini 2.5 Flash" },
  { value: "gemini/gemini-3-flash-preview", label: "Gemini 3 Flash Preview" },
  { value: "gemini/gemini-2.5-pro", label: "Gemini 2.5 Pro" },
];

const SUGGESTED_PROMPTS = [
  "Create a policy that requires opt-in consent for marketing data uses",
  "I need a policy to block advertising data collection in California",
  "Help me create a policy for sensitive health data processing",
  "Create a DENY rule for third-party data sharing without consent",
];

interface ChatMessageBubbleProps {
  message: ChatMessage;
}

const ChatMessageBubble: React.FC<ChatMessageBubbleProps> = ({ message }) => {
  const isUser = message.role === "user";

  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        marginBottom: "16px",
      }}
    >
      <div
        style={{
          maxWidth: "80%",
          padding: "12px 16px",
          borderRadius: "12px",
          backgroundColor: isUser ? "#1890ff" : "#f0f0f0",
          color: isUser ? "white" : "black",
        }}
      >
        {isUser ? (
          <Text
            style={{
              color: "white",
              whiteSpace: "pre-wrap",
            }}
          >
            {message.content}
          </Text>
        ) : (
          <div className={modalStyles.markdownContent}>
            <Markdown>{message.content}</Markdown>
          </div>
        )}
        <div
          style={{
            marginTop: "4px",
            fontSize: "11px",
            opacity: 0.7,
            textAlign: "right",
          }}
        >
          {message.timestamp.toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};

export const PolicyV2ChatModal: React.FC<PolicyV2ChatModalProps> = ({
  isOpen,
  onClose,
  onPolicyGenerated,
}) => {
  const toast = useToast();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [selectedModel, setSelectedModel] = useState(
    "gemini/gemini-3-flash-preview"
  );
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [generatedPolicy, setGeneratedPolicy] =
    useState<PolicyV2Create | null>(null);

  const chatContainerRef = useRef<HTMLDivElement>(null);

  const [sendChat, { isLoading: isSending }] = useSendPolicyV2ChatMutation();
  const [clearChat] = useClearPolicyV2ChatMutation();

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop =
        chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = useCallback(async () => {
    if (!inputMessage.trim() || isSending) return;

    const userMessage: ChatMessage = {
      role: "user",
      content: inputMessage.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");

    try {
      const response = await sendChat({
        message: userMessage.content,
        session_id: sessionId,
        model: selectedModel,
      }).unwrap();

      setSessionId(response.session_id);

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: response.assistant_message,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      if (response.generated_policy) {
        setGeneratedPolicy(response.generated_policy as PolicyV2Create);
      }

      if (response.is_policy_complete && response.generated_policy) {
        toast(successToastParams("Policy generated! Review and save when ready."));
      }
    } catch (error) {
      console.error("Failed to send message:", error);
      toast(errorToastParams("Failed to send message. Please try again."));
    }
  }, [inputMessage, isSending, sendChat, sessionId, selectedModel, toast]);

  const handleClose = useCallback(() => {
    if (sessionId) {
      clearChat(sessionId);
    }
    setMessages([]);
    setSessionId(null);
    setGeneratedPolicy(null);
    setInputMessage("");
    onClose();
  }, [sessionId, clearChat, onClose]);

  const handleUsePolicy = useCallback(() => {
    if (generatedPolicy) {
      onPolicyGenerated(generatedPolicy);
      handleClose();
    }
  }, [generatedPolicy, onPolicyGenerated, handleClose]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInputMessage(suggestion);
  };

  const handleClearHistory = useCallback(async () => {
    if (sessionId) {
      try {
        await clearChat(sessionId).unwrap();
        setMessages([]);
        setSessionId(null);
        setGeneratedPolicy(null);
        toast(successToastParams("Chat history cleared"));
      } catch (error) {
        console.error("Failed to clear history:", error);
        toast(errorToastParams("Failed to clear chat history."));
      }
    }
  }, [sessionId, clearChat, toast]);

  return (
    <Modal
      title={
        <Flex justify="space-between" align="center">
          <Title level={4} style={{ margin: 0 }}>
            AI Policy Builder
          </Title>
          <Space>
            <Select
              value={selectedModel}
              onChange={setSelectedModel}
              options={AI_MODELS}
              style={{ width: 180 }}
              size="small"
            />
            <Tooltip title="Clear chat history">
              <Button
                size="small"
                onClick={handleClearHistory}
                disabled={messages.length === 0}
              >
                Clear
              </Button>
            </Tooltip>
          </Space>
        </Flex>
      }
      open={isOpen}
      onCancel={handleClose}
      footer={null}
      width={900}
      style={{ top: 20 }}
    >
      <div style={{ height: "600px", display: "flex", flexDirection: "column" }}>
        {/* Chat History */}
        <div
          ref={chatContainerRef}
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "16px",
            border: "1px solid #d9d9d9",
            borderRadius: "6px",
            backgroundColor: "#fafafa",
            marginBottom: "16px",
          }}
        >
          {messages.length === 0 ? (
            <div style={{ textAlign: "center", padding: "40px", color: "#666" }}>
              <Title level={5}>Create a Policy with AI</Title>
              <Paragraph>
                Describe what you want your policy to do, and I'll help you
                build it. You can specify what data uses should be allowed or
                denied, and under what conditions.
              </Paragraph>
              <Divider />
              <Text strong>Try one of these to get started:</Text>
              <Space
                direction="vertical"
                style={{ marginTop: "12px", width: "100%" }}
              >
                {SUGGESTED_PROMPTS.map((prompt) => (
                  <Button
                    key={prompt}
                    type="link"
                    size="small"
                    onClick={() => handleSuggestionClick(prompt)}
                    style={{ textAlign: "left", padding: "4px 8px" }}
                  >
                    &quot;{prompt}&quot;
                  </Button>
                ))}
              </Space>
            </div>
          ) : (
            messages.map((msg, index) => (
              <ChatMessageBubble key={index} message={msg} />
            ))
          )}
          {isSending && (
            <div style={{ textAlign: "center", padding: "20px" }}>
              <Spin size="small" />
              <div style={{ marginTop: "8px" }}>Thinking...</div>
            </div>
          )}
        </div>

        {/* Generated Policy Preview */}
        {generatedPolicy && (
          <Alert
            type="success"
            showIcon
            style={{ marginBottom: "16px" }}
            message={
              <Flex justify="space-between" align="center">
                <div>
                  <Text strong>Generated Policy: {generatedPolicy.name}</Text>
                  <br />
                  <Text type="secondary">
                    {generatedPolicy.rules?.length || 0} rule(s) &bull; Key:{" "}
                    {generatedPolicy.fides_key}
                  </Text>
                </div>
                <Button type="primary" onClick={handleUsePolicy}>
                  Use This Policy
                </Button>
              </Flex>
            }
          />
        )}

        {/* Message Input */}
        <Space.Compact style={{ width: "100%" }}>
          <TextArea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Describe what you want your policy to do... (Press Enter to send, Shift+Enter for new line)"
            autoSize={{ minRows: 2, maxRows: 4 }}
            disabled={isSending}
            style={{ flex: 1 }}
          />
          <Button
            type="primary"
            onClick={handleSend}
            loading={isSending}
            disabled={!inputMessage.trim()}
            style={{ height: "auto" }}
          >
            Send
          </Button>
        </Space.Compact>
      </div>
    </Modal>
  );
};

export default PolicyV2ChatModal;
