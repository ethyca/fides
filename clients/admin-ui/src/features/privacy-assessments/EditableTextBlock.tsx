import classNames from "classnames";
import {
  Button,
  CheckOutlined,
  CloseOutlined,
  Flex,
  Form,
  Icons,
  Input,
  Typography,
} from "fidesui";
import { useState } from "react";

import styles from "./EditableTextBlock.module.scss";

interface EditableTextBlockProps {
  value: string;
  onSave?: (value: string) => Promise<void> | void;
  isLoading?: boolean;
  placeholder?: string;
  readOnly?: boolean;
  className?: string;
}

export const EditableTextBlock = ({
  value,
  onSave,
  isLoading = false,
  placeholder,
  readOnly = false,
  className,
}: EditableTextBlockProps) => {
  const [isEditing, setIsEditing] = useState(false);

  const handleFinish = async ({ content }: { content: string }) => {
    await onSave?.(content);
    setIsEditing(false);
  };

  if (isEditing) {
    return (
      <Form
        initialValues={{ content: value }}
        onFinish={handleFinish}
        className={className}
      >
        <Form.Item name="content" noStyle>
          <Input.TextArea
            autoFocus
            placeholder={placeholder}
            rows={4}
            size="middle"
          />
        </Form.Item>
        <Flex justify="flex-end" gap="small" className="my-2">
          <Button
            type="text"
            icon={<CloseOutlined />}
            onClick={() => setIsEditing(false)}
            size="small"
          >
            Cancel
          </Button>
          <Button
            type="primary"
            icon={<CheckOutlined />}
            htmlType="submit"
            size="small"
            loading={isLoading}
          >
            Save
          </Button>
        </Flex>
      </Form>
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
      {value || <span className={styles.placeholder}>{placeholder}</span>}
    </Typography.Paragraph>
  );
};
