import React, { useState, useRef, useEffect } from "react";
import {
  AntModal as Modal,
  AntInput as Input,
  AntButton as Button,
  AntSpace as Space,
  AntTypography as Typography,
  AntSpin as Spin,
  AntMessage as Message,
  AntFlex as Flex,
  AntDivider as Divider,
  AntSelect as Select,
  AntTooltip as Tooltip,
} from "fidesui";

const { TextArea } = Input;
const { Text, Title } = Typography;

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import {
  selectSelectedAssessmentId,
  setShowAssessmentChatModal,
  useSendChatMessageMutation,
  useGetChatHistoryQuery,
  useClearChatHistoryMutation,
  ChatHistoryItem,
} from "./assessments.slice";

const AI_MODELS = [
  { value: "gemini/gemini-1.5-pro-latest", label: "Gemini 1.5 Pro" },
  { value: "gemini/gemini-1.5-flash-latest", label: "Gemini 1.5 Flash" },
  { value: "gemini/gemini-2.0-flash-exp", label: "Gemini 2.0 Flash (Experimental)" },
  { value: "custom", label: "Custom model..." },
];

interface ChatMessageProps {
  message: ChatHistoryItem;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
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
        <Text style={{ color: isUser ? "white" : "inherit" }}>
          {message.content}
        </Text>
        <div
          style={{
            marginTop: "4px",
            fontSize: "11px",
            opacity: 0.7,
            textAlign: "right",
          }}
        >
          {new Date(message.created_at).toLocaleTimeString()}
          {message.model_used && !isUser && (
            <span style={{ marginLeft: "8px" }}>({message.model_used})</span>
          )}
        </div>
      </div>
    </div>
  );
};

export const AssessmentChatModal: React.FC = () => {
  const dispatch = useAppDispatch();
  const { showAssessmentChatModal } = useAppSelector(
    (state) => state.assessments
  );
  const selectedAssessmentId = useAppSelector(selectSelectedAssessmentId);

  const [message, setMessage] = useState("");
  const [selectedModel, setSelectedModel] = useState<string>("gemini/gemini-1.5-pro-latest");
  const [customModel, setCustomModel] = useState<string>("");
  const [showCustomInput, setShowCustomInput] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  const { data: chatHistory, isLoading: historyLoading } = useGetChatHistoryQuery(
    selectedAssessmentId || "",
    {
      skip: !selectedAssessmentId || !showAssessmentChatModal,
    }
  );

  const [sendChatMessage, { isLoading: sendingMessage }] =
    useSendChatMessageMutation();
  const [clearChatHistory, { isLoading: clearingHistory }] =
    useClearChatHistoryMutation();

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [chatHistory?.messages]);

  const handleClose = () => {
    dispatch(setShowAssessmentChatModal(false));
    setMessage("");
  };

  const handleSendMessage = async () => {
    if (!message.trim() || !selectedAssessmentId || sendingMessage) {
      return;
    }

    // Use custom model if "custom" is selected and custom model is provided
    const modelToUse = selectedModel === "custom" ? customModel : selectedModel;
    
    if (!modelToUse?.trim()) {
      Message.error("Please enter a custom model name");
      return;
    }

    try {
      await sendChatMessage({
        assessmentId: selectedAssessmentId,
        message: message.trim(),
        model: modelToUse,
      }).unwrap();
      
      setMessage("");
      Message.success("Message sent successfully");
    } catch (error) {
      console.error("Failed to send message:", error);
      Message.error("Failed to send message. Please try again.");
    }
  };

  const handleClearHistory = async () => {
    if (!selectedAssessmentId || clearingHistory) {
      return;
    }

    try {
      await clearChatHistory(selectedAssessmentId).unwrap();
      Message.success("Chat history cleared");
    } catch (error) {
      console.error("Failed to clear history:", error);
      Message.error("Failed to clear chat history. Please try again.");
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const suggestedQuestions = [
    "What assessments need to be completed?",
    "Help me understand this privacy risk",
    "What information do I need to answer these questions?",
    "Explain the compliance requirements for this dataset",
  ];

  const handleSuggestionClick = (suggestion: string) => {
    setMessage(suggestion);
  };

  return (
    <Modal
      title={
        <Flex justify="space-between" align="center">
          <Title level={4} style={{ margin: 0 }}>
            AI Assessment Assistant
          </Title>
          <Space>
            <Select
              value={selectedModel}
              onChange={(value) => {
                setSelectedModel(value);
                setShowCustomInput(value === "custom");
              }}
              options={AI_MODELS}
              style={{ width: 200 }}
              size="small"
            />
            {showCustomInput && (
              <Input
                placeholder="e.g., gemini/gemini-1.5-pro"
                value={customModel}
                onChange={(e) => setCustomModel(e.target.value)}
                style={{ width: 250 }}
                size="small"
              />
            )}
            <Tooltip title="Clear chat history">
              <Button
                size="small"
                loading={clearingHistory}
                onClick={handleClearHistory}
                disabled={!chatHistory?.messages?.length}
              >
                Clear
              </Button>
            </Tooltip>
          </Space>
        </Flex>
      }
      open={showAssessmentChatModal}
      onCancel={handleClose}
      footer={null}
      width={800}
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
          {historyLoading ? (
            <div style={{ textAlign: "center", padding: "20px" }}>
              <Spin size="large" />
              <div style={{ marginTop: "8px" }}>Loading chat history...</div>
            </div>
          ) : chatHistory?.messages?.length ? (
            chatHistory.messages.map((msg, index) => (
              <ChatMessage key={index} message={msg} />
            ))
          ) : (
            <div style={{ textAlign: "center", padding: "40px", color: "#666" }}>
              <Title level={5}>Welcome to AI Assessment Assistant!</Title>
              <Text>
                I'm here to help you complete your privacy assessment. You can ask me
                questions about:
              </Text>
              <ul style={{ textAlign: "left", marginTop: "16px" }}>
                <li>Understanding assessment requirements</li>
                <li>Explaining privacy risks and compliance implications</li>
                <li>Suggesting answers based on your system and dataset context</li>
                <li>Clarifying specific questions in your assessment</li>
              </ul>
              <Divider />
              <Text strong>Try one of these questions to get started:</Text>
              <Space direction="vertical" style={{ marginTop: "12px", width: "100%" }}>
                {suggestedQuestions.map((question, index) => (
                  <Button
                    key={index}
                    type="link"
                    size="small"
                    onClick={() => handleSuggestionClick(question)}
                    style={{ textAlign: "left", padding: "4px 8px" }}
                  >
                    "{question}"
                  </Button>
                ))}
              </Space>
            </div>
          )}
        </div>

        {/* Message Input */}
        <Space.Compact style={{ width: "100%" }}>
          <TextArea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything about this privacy assessment... (Press Enter to send, Shift+Enter for new line)"
            autoSize={{ minRows: 2, maxRows: 4 }}
            disabled={sendingMessage || !selectedAssessmentId}
            style={{ flex: 1 }}
          />
          <Button
            type="primary"
            onClick={handleSendMessage}
            loading={sendingMessage}
            disabled={!message.trim() || !selectedAssessmentId}
            style={{ height: "auto" }}
          >
            Send
          </Button>
        </Space.Compact>
      </div>
    </Modal>
  );
};

export default AssessmentChatModal;