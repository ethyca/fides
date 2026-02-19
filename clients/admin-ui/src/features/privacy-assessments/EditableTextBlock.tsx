import type { TextAreaRef } from "antd/es/input/TextArea";
import classNames from "classnames";
import {
  Button,
  CheckOutlined,
  CloseOutlined,
  Flex,
  Icons,
  Input,
} from "fidesui";
import React, { useCallback, useEffect, useRef, useState } from "react";

import styles from "./EditableTextBlock.module.scss";
import { SlackIcon } from "./SlackIcon";

interface EditableTextBlockProps
  extends Omit<React.HTMLAttributes<HTMLDivElement>, "onChange"> {
  value: string;
  onChange: (value: string) => void;
  onSave?: (value: string) => void;
  placeholder?: string;
  readOnly?: boolean;
  showEditButton?: boolean;
  onComment?: (selection: { text: string; start: number; end: number }) => void;
  onRequestInput?: (selection: {
    text: string;
    start: number;
    end: number;
  }) => void;
  renderContent?: (text: string) => React.ReactNode;
}

export const EditableTextBlock = ({
  value,
  onChange,
  onSave,
  placeholder = "Click to edit...",
  readOnly = false,
  showEditButton = true,
  onComment,
  onRequestInput,
  renderContent,
  className,
  ...props
}: EditableTextBlockProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value);
  const [selectedText, setSelectedText] = useState<{
    text: string;
    start: number;
    end: number;
  } | null>(null);
  const [toolbarPosition, setToolbarPosition] = useState<{
    x: number;
    y: number;
  } | null>(null);
  const textRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<TextAreaRef>(null);

  useEffect(() => {
    setEditValue(value);
  }, [value]);

  useEffect(() => {
    if (isEditing && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [isEditing]);

  const handleSave = () => {
    onChange(editValue);
    setIsEditing(false);
    if (onSave) {
      onSave(editValue);
    }
  };

  const handleCancel = () => {
    setEditValue(value);
    setIsEditing(false);
  };

  const handleTextSelection = useCallback(() => {
    if (isEditing) {
      setSelectedText(null);
      setToolbarPosition(null);
      return;
    }

    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) {
      setSelectedText(null);
      setToolbarPosition(null);
      return;
    }

    const text = selection.toString().trim();
    if (text.length === 0) {
      setSelectedText(null);
      setToolbarPosition(null);
      return;
    }

    const range = selection.getRangeAt(0);
    if (
      !textRef.current ||
      !textRef.current.contains(range.commonAncestorContainer)
    ) {
      setSelectedText(null);
      setToolbarPosition(null);
      return;
    }

    const rect = range.getBoundingClientRect();
    setToolbarPosition({
      x: rect.left + rect.width / 2,
      y: rect.top - 10,
    });

    const textContent = textRef.current.textContent || "";
    const start = textContent.indexOf(text);
    const end = start + text.length;

    setSelectedText({ text, start, end });
  }, [isEditing]);

  const handleComment = () => {
    if (selectedText && onComment) {
      onComment(selectedText);
      window.getSelection()?.removeAllRanges();
      setSelectedText(null);
      setToolbarPosition(null);
    }
  };

  const handleRequestInput = () => {
    if (selectedText && onRequestInput) {
      onRequestInput(selectedText);
      window.getSelection()?.removeAllRanges();
      setSelectedText(null);
      setToolbarPosition(null);
    }
  };

  useEffect(() => {
    document.addEventListener("selectionchange", handleTextSelection);
    const handleClickOutside = (e: MouseEvent) => {
      if (textRef.current && !textRef.current.contains(e.target as Node)) {
        const selection = window.getSelection();
        if (selection && selection.toString().trim().length === 0) {
          setSelectedText(null);
          setToolbarPosition(null);
        }
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("selectionchange", handleTextSelection);
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [handleTextSelection]);

  if (isEditing) {
    return (
      <div className={className} {...props}>
        <Input.TextArea
          ref={textareaRef}
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          placeholder={placeholder}
          rows={4}
          className={styles.textarea}
        />
        <Flex justify="flex-end" gap="small">
          <Button
            type="text"
            icon={<CloseOutlined />}
            onClick={handleCancel}
            size="small"
          >
            Cancel
          </Button>
          <Button
            type="primary"
            icon={<CheckOutlined />}
            onClick={handleSave}
            size="small"
          >
            Save
          </Button>
        </Flex>
      </div>
    );
  }

  return (
    <div className={classNames(styles.root, className)} {...props}>
      {showEditButton && !readOnly && (
        <Button
          type="text"
          icon={<Icons.Edit size={16} />}
          size="small"
          onClick={() => setIsEditing(true)}
          className={styles.editButton}
          aria-label="Edit"
        />
      )}

      <div
        ref={textRef}
        className={classNames(styles.content, {
          [styles.contentWithEditButton]: showEditButton && !readOnly,
        })}
      >
        {value ? (
          (renderContent?.(value) ?? value)
        ) : (
          <span className={styles.placeholder}>{placeholder}</span>
        )}
      </div>

      {selectedText && toolbarPosition && (
        <div
          className={styles.selectionToolbar}
          style={{
            left: `${toolbarPosition.x}px`,
            top: `${toolbarPosition.y}px`,
          }}
          onMouseDown={(e) => e.preventDefault()}
          role="toolbar"
          aria-label="Text actions"
        >
          {onComment && (
            <Button
              type="text"
              size="small"
              icon={<Icons.Chat size={14} />}
              onClick={handleComment}
              className={styles.toolbarButton}
            >
              Comment
            </Button>
          )}
          {onRequestInput && (
            <Button
              type="text"
              size="small"
              icon={<SlackIcon size={14} />}
              onClick={handleRequestInput}
              className={styles.toolbarButton}
            >
              Request input from team
            </Button>
          )}
        </div>
      )}
    </div>
  );
};
