import { CheckOutlined, CloseOutlined, CommentOutlined } from "@ant-design/icons";
import type { TextAreaRef } from "antd/es/input/TextArea";
import { Button, Flex, Icons, Input } from "fidesui";

import { SlackIcon } from "./SlackIcon";
import palette from "fidesui/src/palette/palette.module.scss";
import React, { useEffect, useRef, useState } from "react";

interface EditableTextBlockProps {
  value: string;
  onChange: (value: string) => void;
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
  style?: React.CSSProperties;
}

export const EditableTextBlock: React.FC<EditableTextBlockProps> = ({
  value,
  onChange,
  placeholder = "Click to edit...",
  readOnly = false,
  showEditButton = true,
  onComment,
  onRequestInput,
  renderContent,
  style,
}) => {
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
  };

  const handleCancel = () => {
    setEditValue(value);
    setIsEditing(false);
  };

  const handleTextSelection = () => {
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

  if (isEditing) {
    return (
      <div style={style}>
        <Input.TextArea
          ref={textareaRef}
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          placeholder={placeholder}
          rows={4}
          style={{
            marginBottom: 8,
            fontFamily: "inherit",
            fontSize: "inherit",
            lineHeight: 1.6,
          }}
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
    <div style={{ position: "relative", ...style }}>
      {showEditButton && !readOnly && !isEditing && (
        <Button
          type="text"
          icon={<Icons.Edit size={16} />}
          size="small"
          onClick={() => setIsEditing(true)}
          style={{
            position: "absolute",
            top: 8,
            right: 8,
            zIndex: 10,
            padding: "4px 8px",
            borderRadius: 4,
            backgroundColor: "transparent",
            transition: "all 0.2s ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = palette.FIDESUI_BG_CORINTH;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "transparent";
          }}
        />
      )}

      <div
        ref={textRef}
        style={{
          padding: style?.padding || "8px 12px",
          minHeight: style?.minHeight === "auto" ? "auto" : 60,
          borderRadius: 6,
          border: readOnly ? "none" : `1px solid transparent`,
          cursor: "text",
          transition: "all 0.2s ease",
          position: "relative",
          lineHeight: 1.6,
          color: value ? "inherit" : palette.FIDESUI_NEUTRAL_500,
          paddingRight:
            showEditButton && !readOnly ? 40 : style?.paddingRight || 12,
          display: style?.display || "block",
          ...style,
        }}
      >
        {value ? (
          renderContent ? (
            renderContent(value)
          ) : (
            value
          )
        ) : (
          <span
            style={{ fontStyle: "italic", color: palette.FIDESUI_NEUTRAL_400 }}
          >
            {placeholder}
          </span>
        )}
      </div>

      {selectedText && toolbarPosition && (
        <div
          style={{
            position: "fixed",
            left: `${toolbarPosition.x}px`,
            top: `${toolbarPosition.y}px`,
            transform: "translate(-50%, -100%)",
            backgroundColor: "#FFFFFF",
            border: `1px solid ${palette.FIDESUI_NEUTRAL_200}`,
            borderRadius: 6,
            padding: "4px",
            boxShadow: "0 4px 12px rgba(0, 0, 0, 0.15)",
            zIndex: 1000,
            display: "flex",
            gap: 4,
            marginBottom: 8,
            alignItems: "center",
          }}
          onMouseDown={(e) => e.preventDefault()}
          onClick={(e) => e.stopPropagation()}
        >
          {onComment && (
            <Button
              type="text"
              size="small"
              icon={<CommentOutlined style={{ fontSize: 14 }} />}
              onClick={handleComment}
              style={{
                fontSize: 13,
                display: "flex",
                alignItems: "center",
                gap: 6,
                padding: "6px 12px",
                borderRadius: 4,
                height: "auto",
                fontWeight: 500,
              }}
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
              style={{
                fontSize: 13,
                display: "flex",
                alignItems: "center",
                gap: 6,
                padding: "6px 12px",
                borderRadius: 4,
                height: "auto",
                fontWeight: 500,
              }}
            >
              Request input from team
            </Button>
          )}
        </div>
      )}
    </div>
  );
};
