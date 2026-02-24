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
import React, { useEffect, useRef, useState } from "react";

import styles from "./EditableTextBlock.module.scss";

interface EditableTextBlockProps
  extends Omit<React.HTMLAttributes<HTMLDivElement>, "onChange"> {
  value: string;
  onChange: (value: string) => void;
  onSave?: (value: string) => void;
  placeholder?: string;
  readOnly?: boolean;
  showEditButton?: boolean;
  renderContent?: (text: string) => React.ReactNode;
}

export const EditableTextBlock = ({
  value,
  onChange,
  onSave,
  placeholder = "Click to edit...",
  readOnly = false,
  showEditButton = true,
  renderContent,
  className,
  ...props
}: EditableTextBlockProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value);
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
    </div>
  );
};
