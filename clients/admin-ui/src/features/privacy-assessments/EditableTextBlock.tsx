import classNames from "classnames";
import {
  Button,
  CheckOutlined,
  CloseOutlined,
  Flex,
  Icons,
  Input,
  Typography,
} from "fidesui";
import { useEffect, useState } from "react";

import styles from "./EditableTextBlock.module.scss";

interface EditableTextBlockProps {
  value: string;
  onSave?: (value: string) => Promise<void> | void;
  isLoading?: boolean;
  placeholder?: string;
  readOnly?: boolean;
  renderContent?: (text: string) => React.ReactNode;
  className?: string;
}

export const EditableTextBlock = ({
  value,
  onSave,
  isLoading = false,
  placeholder,
  readOnly = false,
  renderContent,
  className,
}: EditableTextBlockProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value);

  useEffect(() => {
    if (!isEditing) {
      setEditValue(value);
    }
  }, [value, isEditing]);

  const handleSave = async () => {
    await onSave?.(editValue);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditValue(value);
    setIsEditing(false);
  };

  if (isEditing) {
    return (
      <div className={className}>
        <Input.TextArea
          autoFocus
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          placeholder={placeholder}
          rows={4}
          size="middle"
        />
        <Flex justify="flex-end" gap="small" className="my-2">
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
            loading={isLoading}
          >
            Save
          </Button>
        </Flex>
      </div>
    );
  }

  return (
    <Typography.Paragraph
      className={classNames(styles.root, className)}
      editable={
        !readOnly
          ? {
              icon: <Icons.Edit size={16} className={styles.editIcon} />,
              editing: false,
              onStart: () => setIsEditing(true),
              tooltip: false,
            }
          : false
      }
      size="lg"
    >
      {value ? (
        (renderContent?.(value) ?? value)
      ) : (
        <span className={styles.placeholder}>{placeholder}</span>
      )}
    </Typography.Paragraph>
  );
};
