import { Button, Col, Form, Icons, Input, Row, Text } from "fidesui";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

import { useSubmitPrivacyPolicyMutation } from "./access-policies.slice";

interface PrivacyPolicySectionProps {
  policyUrl: string;
  onUrlChange: (url: string) => void;
}

const PrivacyPolicySection = ({
  policyUrl,
  onUrlChange,
}: PrivacyPolicySectionProps) => {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [submitPolicy, { isLoading }] = useSubmitPrivacyPolicyMutation();

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (!file) return;
      setUploadedFile(file);

      const formData = new FormData();
      formData.append("file", file);
      submitPolicy(formData);
    },
    [submitPolicy],
  );

  const handleSubmitUrl = () => {
    if (!policyUrl.trim()) return;
    const formData = new FormData();
    formData.append("url", policyUrl);
    submitPolicy(formData);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        [".docx"],
    },
    maxSize: 10 * 1024 * 1024,
    multiple: false,
  });

  return (
    <div>
      <Form.Item label="Privacy policy analysis" className="!mb-0">
        <Row gutter={24}>
          <Col span={12}>
            <div
              {...getRootProps()}
              className="flex h-40 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-neutral-4 bg-neutral-1 transition-colors hover:border-neutral-6"
              style={
                isDragActive
                  ? { borderColor: "#000", backgroundColor: "#f5f5f5" }
                  : undefined
              }
            >
              <input {...getInputProps()} />
              {uploadedFile ? (
                <>
                  <Icons.CheckmarkFilled size={24} className="mb-2 text-green-600" />
                  <div className="text-sm font-semibold">{uploadedFile.name}</div>
                  <Text type="secondary" size="sm">
                    {isLoading ? "Uploading..." : "Click or drop to replace"}
                  </Text>
                </>
              ) : (
                <>
                  <Icons.Upload size={24} className="mb-2 text-neutral-6" />
                  <div className="text-sm font-semibold">Upload policy</div>
                  <div className="text-xs text-neutral-6">
                    PDF, DOCX up to 10MB
                  </div>
                </>
              )}
            </div>
          </Col>
          <Col span={12}>
            <Form.Item label="Policy URL" className="!mb-0">
              <Input
                placeholder="https://company.com/privacy"
                value={policyUrl}
                onChange={(e) => onUrlChange(e.target.value)}
                suffix={<Icons.Link size={16} />}
              />
            </Form.Item>
            <Button
              className="mt-2"
              size="small"
              disabled={!policyUrl.trim() || isLoading}
              loading={isLoading}
              onClick={handleSubmitUrl}
            >
              Submit URL
            </Button>
            <div className="mt-2 text-xs text-neutral-6">
              Providing your policy allows Fides to auto-align discovery
              findings with your public commitments.
            </div>
          </Col>
        </Row>
      </Form.Item>
    </div>
  );
};

export default PrivacyPolicySection;
