import {
  AntButton as Button,
  AntFlex as Flex,
  AntInput as Input,
  AntTabs as Tabs,
  AntTabsProps as TabsProps,
} from "fidesui";
import { useEffect, useRef, useState } from "react";

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

  // Focus the textarea when the component mounts
  useEffect(() => {
    if (textAreaRef.current) {
      textAreaRef.current.focus();
    }
  }, []);

  const handleSubmit = () => {
    if (commentText.trim()) {
      // Just log the comment for now
      console.log("Comment submitted:", {
        privacyRequestId,
        commentText,
      });

      // Reset and close
      setCommentText("");
      onCancel();
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
            placeholder="Add a note about this privacy request..."
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
