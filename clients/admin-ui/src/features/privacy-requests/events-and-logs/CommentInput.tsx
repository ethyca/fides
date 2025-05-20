import {
  AntButton as Button,
  AntFlex as Flex,
  AntInput as Input,
  AntMessage as message,
  AntTabs as Tabs,
  AntTabsProps as TabsProps,
} from "fidesui";
import { useEffect, useRef, useState } from "react";

import { CommentType } from "~/types/api/models/CommentType";

import { useCreateCommentMutation } from "../comments/privacy-request-comments.slice";

export interface CommentInputProps {
  privacyRequestId: string;
  onCancel: () => void;
}

export const CommentInput = ({
  privacyRequestId,
  onCancel,
}: CommentInputProps) => {
  const [commentText, setCommentText] = useState("");
  const textAreaRef = useRef<any>(null);
  const [createComment, { isLoading }] = useCreateCommentMutation();

  // Focus the textarea when the component mounts
  useEffect(() => {
    if (textAreaRef.current) {
      textAreaRef.current.focus();
    }
  }, []);

  const handleSubmit = async () => {
    if (commentText.trim()) {
      try {
        await createComment({
          privacy_request_id: privacyRequestId,
          comment_text: commentText,
          comment_type: CommentType.NOTE,
        }).unwrap();

        // Reset and close
        setCommentText("");
        onCancel();
      } catch (error) {
        // eslint-disable-next-line no-console
        console.error("Failed to add comment:", error);
        message.error({
          content: "Failed to add comment",
          duration: 5,
        });
      }
    }
  };

  const items: TabsProps["items"] = [
    {
      key: "internal",
      label: "Internal comment",
      children: (
        <div className="py-2">
          <Input.TextArea
            ref={textAreaRef}
            value={commentText}
            onChange={(e) => setCommentText(e.target.value)}
            rows={3}
            className="mb-4 w-full"
            data-testid="comment-input"
          />
        </div>
      ),
    },
  ];

  return (
    <div>
      <Tabs items={items} />

      <Flex justify="flex-end" className="mt-4 gap-2">
        <Button onClick={onCancel} data-testid="cancel-comment-button">
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          loading={isLoading}
          disabled={!commentText.trim()}
          type="primary"
          htmlType="button"
          data-testid="submit-comment-button"
        >
          Save
        </Button>
      </Flex>
    </div>
  );
};
