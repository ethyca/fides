import type { UploadProps } from "fidesui";
import { Button, Flex, Icons, Typography, Upload } from "fidesui";
import { useState } from "react";

const MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024;

const readFileAsDataUrl = (file: File) =>
  new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });

interface ImageUploadFieldProps {
  value?: string;
  onChange?: (value: string) => void;
  ariaLabel?: string;
}

export const ImageUploadField = ({
  value,
  onChange,
  ariaLabel,
}: ImageUploadFieldProps) => {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleBeforeUpload: UploadProps["beforeUpload"] = async (file) => {
    setErrorMessage(null);
    if (!file.type.startsWith("image/")) {
      setErrorMessage("File must be an image.");
      return false;
    }
    if (file.size > MAX_FILE_SIZE_BYTES) {
      setErrorMessage("File must be 2MB or smaller.");
      return false;
    }
    try {
      const dataUrl = await readFileAsDataUrl(file);
      onChange?.(dataUrl);
    } catch {
      setErrorMessage("Failed to read file.");
    }
    return false;
  };

  const handleRemove = () => {
    setErrorMessage(null);
    onChange?.("");
  };

  return (
    <Flex vertical gap="small">
      <Upload.Dragger
        accept="image/*"
        beforeUpload={handleBeforeUpload}
        showUploadList={false}
        multiple={false}
        aria-label={ariaLabel}
      >
        {value ? (
          <Flex vertical align="center" gap="small" className="p-2">
            <img
              src={value}
              alt=""
              className="max-h-24 max-w-full object-contain"
            />
            <Typography.Text type="secondary">
              Click or drag to replace
            </Typography.Text>
          </Flex>
        ) : (
          <Flex vertical align="center" gap="small" className="p-4">
            <Icons.Upload size={32} />
            <Typography.Text>
              Click or drag an image here to upload
            </Typography.Text>
            <Typography.Text type="secondary" className="text-xs">
              PNG, JPG, or SVG up to 2MB
            </Typography.Text>
          </Flex>
        )}
      </Upload.Dragger>
      {value && (
        <Flex justify="flex-end">
          <Button size="small" onClick={handleRemove}>
            Remove
          </Button>
        </Flex>
      )}
      {errorMessage && (
        <Typography.Text type="danger">{errorMessage}</Typography.Text>
      )}
    </Flex>
  );
};
