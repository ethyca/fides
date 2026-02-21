import React, { useState, useRef, useEffect, useCallback } from "react";
import { Button, Select, Tooltip, useChakraToast as useToast } from "fidesui";

import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  useSendPolicyV2ChatMutation,
  useClearPolicyV2ChatMutation,
} from "../../policy-v2.slice";
import { PolicyV2Create } from "../../types";
import { ChatInput } from "./ChatInput";
import { ChatMessage, ChatMessageData } from "./ChatMessage";
import styles from "./AIChatPane.module.scss";

const AI_MODELS = [
  { value: "gemini/gemini-2.5-flash", label: "Gemini 2.5 Flash" },
  { value: "gemini/gemini-3-flash-preview", label: "Gemini 3 Flash" },
  { value: "gemini/gemini-2.5-pro", label: "Gemini 2.5 Pro" },
];

const SUGGESTED_PROMPTS = [
  "Create a policy that requires opt-in consent for marketing",
  "Block advertising data collection in California",
  "Create a DENY rule for third-party sharing without consent",
  "Block data use if sourced from a third-party data broker",
  "Help me create a policy for sensitive health data",
];

interface AIChatPaneProps {
  onPolicyGenerated: (policy: PolicyV2Create) => void;
  onPolicySave: (policy: PolicyV2Create) => void;
  generatedPolicy: PolicyV2Create | null;
  hasExistingPolicy?: boolean;
}

export const AIChatPane = ({
  onPolicyGenerated,
  onPolicySave,
  generatedPolicy,
  hasExistingPolicy,
}: AIChatPaneProps) => {
  const toast = useToast();
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [selectedModel, setSelectedModel] = useState("gemini/gemini-3-flash-preview");
  const [sessionId, setSessionId] = useState<string | null>(null);

  const messagesContainerRef = useRef<HTMLDivElement>(null);

  const [sendChat, { isLoading: isSending }] = useSendPolicyV2ChatMutation();
  const [clearChat] = useClearPolicyV2ChatMutation();

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop =
        messagesContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = useCallback(async () => {
    if (!inputMessage.trim() || isSending) return;

    const userMessage: ChatMessageData = {
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

      const assistantMessage: ChatMessageData = {
        role: "assistant",
        content: response.assistant_message,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      if (response.generated_policy) {
        onPolicyGenerated(response.generated_policy as PolicyV2Create);
      }

      if (response.is_policy_complete && response.generated_policy) {
        toast(
          successToastParams("Policy generated! Review the flow and save when ready.")
        );
      }
    } catch (error) {
      console.error("Failed to send message:", error);
      toast(errorToastParams("Failed to send message. Please try again."));
    }
  }, [inputMessage, isSending, sendChat, sessionId, selectedModel, toast, onPolicyGenerated]);

  const handleClearHistory = useCallback(async () => {
    if (sessionId) {
      try {
        await clearChat(sessionId).unwrap();
        setMessages([]);
        setSessionId(null);
        onPolicyGenerated(null as unknown as PolicyV2Create);
        toast(successToastParams("Chat history cleared"));
      } catch (error) {
        console.error("Failed to clear history:", error);
        toast(errorToastParams("Failed to clear chat history."));
      }
    } else {
      setMessages([]);
      onPolicyGenerated(null as unknown as PolicyV2Create);
    }
  }, [sessionId, clearChat, toast, onPolicyGenerated]);

  const handleSuggestionClick = (suggestion: string) => {
    setInputMessage(suggestion);
  };

  const handleSavePolicy = useCallback(() => {
    if (generatedPolicy) {
      onPolicySave(generatedPolicy);
    }
  }, [generatedPolicy, onPolicySave]);

  const ruleCount = generatedPolicy?.rules?.length || 0;

  return (
    <div className={styles.chatPane}>
      {/* Header with model selector */}
      <div className={styles.header}>
        <span className={styles.title}>AI Policy Builder</span>
        <div className={styles.headerActions}>
          <Select
            className={styles.modelSelect}
            size="small"
            value={selectedModel}
            onChange={setSelectedModel}
            options={AI_MODELS}
            style={{ width: 140 }}
          />
          <Tooltip title="Clear chat history">
            <Button
              className={styles.clearButton}
              size="small"
              onClick={handleClearHistory}
              disabled={messages.length === 0}
            >
              Clear
            </Button>
          </Tooltip>
        </div>
      </div>

      {/* Messages area */}
      <div ref={messagesContainerRef} className={styles.messagesContainer}>
        {messages.length === 0 ? (
          <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>AI</div>
            <h3 className={styles.emptyTitle}>Create a Policy with AI</h3>
            <p className={styles.emptyDescription}>
              Describe what you want your policy to do. The flow will update in
              real-time as the AI builds your policy.
            </p>
            <p className={styles.suggestionsTitle}>Try one of these</p>
            <div className={styles.suggestionsList}>
              {SUGGESTED_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  className={styles.suggestionButton}
                  onClick={() => handleSuggestionClick(prompt)}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, index) => (
              <ChatMessage key={index} message={msg} />
            ))}
            {isSending && (
              <div className={styles.loadingIndicator}>
                <div className={styles.spinner} />
                <span>Thinking...</span>
              </div>
            )}
          </>
        )}
      </div>

      {/* Policy preview card */}
      {generatedPolicy && (
        <div className={styles.policyPreview}>
          <div className={styles.policyPreviewHeader}>
            <span className={styles.policyPreviewIcon}>&#10003;</span>
            <span className={styles.policyPreviewTitle}>Policy Generated</span>
          </div>
          <div className={styles.policyPreviewDetails}>
            <p className={styles.policyName}>{generatedPolicy.name}</p>
            <p className={styles.policyMeta}>
              {ruleCount} {ruleCount === 1 ? "rule" : "rules"} &bull;{" "}
              {generatedPolicy.fides_key}
            </p>
          </div>
          <div className={styles.policyActions}>
            <Button
              type="primary"
              size="small"
              onClick={handleSavePolicy}
              disabled={hasExistingPolicy}
            >
              {hasExistingPolicy ? "Policy Exists" : "Save Policy"}
            </Button>
          </div>
        </div>
      )}

      {/* Input area */}
      <ChatInput
        value={inputMessage}
        onChange={setInputMessage}
        onSend={handleSend}
        isLoading={isSending}
      />
    </div>
  );
};
