import { Col, Form, Icons, Input, Row } from "fidesui";
import { useCallback } from "react";
import { useDropzone } from "react-dropzone";

interface PrivacyPolicySectionProps {
  policyUrl: string;
  onUrlChange: (url: string) => void;
}

const PrivacyPolicySection = ({
  policyUrl,
  onUrlChange,
}: PrivacyPolicySectionProps) => {
  const onDrop = useCallback(() => {
    // Mock: file upload is a no-op for the prototype
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        [".docx"],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
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
              <Icons.Upload size={24} className="mb-2 text-neutral-6" />
              <div className="text-sm font-semibold">Upload policy</div>
              <div className="text-xs text-neutral-6">PDF, DOCX up to 10MB</div>
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
