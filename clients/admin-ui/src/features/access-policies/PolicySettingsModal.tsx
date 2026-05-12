import type { UploadFile } from "fidesui";
import {
  Button,
  Flex,
  Form,
  Icons,
  Modal,
  Select,
  Spin,
  Text,
  Upload,
  useMessage,
} from "fidesui";
import { useEffect, useMemo, useState } from "react";

import { useGetLocationsRegulationsQuery } from "../locations/locations.slice";
import {
  useGeneratePoliciesMutation,
  useGetOnboardingConfigQuery,
} from "./access-policies.slice";

interface PolicySettingsModalProps {
  open: boolean;
  onClose: () => void;
}

const PolicySettingsModal = ({ open, onClose }: PolicySettingsModalProps) => {
  const message = useMessage();
  const [geographies, setGeographies] = useState<string[]>([]);
  const [policyUrls, setPolicyUrls] = useState<string[]>([]);
  const [policyFiles, setPolicyFiles] = useState<File[]>([]);

  const {
    data: config,
    isLoading: isConfigLoading,
    error: configError,
  } = useGetOnboardingConfigQuery(undefined, { skip: !open });
  const [generatePolicies, { isLoading: isGenerating }] =
    useGeneratePoliciesMutation();
  const { data: locationsData, isLoading: isLocationsLoading } =
    useGetLocationsRegulationsQuery();

  const geographyOptions = useMemo(
    () =>
      (locationsData?.location_groups ?? []).map((g) => ({
        label: g.name,
        value: g.id,
      })),
    [locationsData],
  );

  useEffect(() => {
    if (open) {
      setPolicyUrls([]);
      setPolicyFiles([]);
    }
  }, [open]);

  useEffect(() => {
    if (config) {
      setGeographies(config.geographies);
    }
  }, [config]);

  useEffect(() => {
    if (configError) {
      message.error("Failed to load policy config");
      onClose();
    }
  }, [configError, message, onClose]);

  const handleFileChange = (info: { fileList: UploadFile[] }) => {
    setPolicyFiles(
      info.fileList
        .map((f) => f.originFileObj as File | undefined)
        .filter((f): f is File => !!f),
    );
  };

  const handleSubmit = async () => {
    if (!config?.industry || geographies.length === 0) {
      return;
    }
    const formData = new FormData();
    formData.append("industry", config.industry);
    geographies.forEach((g) => formData.append("geographies", g));
    policyUrls.forEach((u) => formData.append("policy_urls", u));
    policyFiles.forEach((f) => formData.append("files", f));
    try {
      await generatePolicies(formData).unwrap();
      message.success("Policies suggested successfully");
      onClose();
    } catch {
      message.error("Failed to suggest policies");
    }
  };

  return (
    <Modal
      title="Policy settings"
      open={open}
      onCancel={onClose}
      onOk={handleSubmit}
      okText="Suggest additional policies"
      okButtonProps={{ disabled: geographies.length === 0 }}
      confirmLoading={isGenerating}
      destroyOnHidden
      width={640}
    >
      {isConfigLoading ? (
        <div className="flex justify-center py-12">
          <Spin />
        </div>
      ) : (
        <Form layout="vertical" className="!mb-0">
          <Text type="secondary" className="mb-5 block">
            If your operating regions or privacy policies have changed, update
            them here and Fides will suggest additional policies to cover the
            new requirements.
          </Text>

          <Form.Item
            label="Geographies"
            required
            htmlFor="settings-geography-select"
          >
            <Select
              id="settings-geography-select"
              aria-label="Geographies"
              className="w-full"
              mode="multiple"
              placeholder="Select geographies"
              loading={isLocationsLoading}
              value={geographies}
              onChange={setGeographies}
              options={geographyOptions}
              allowClear
            />
          </Form.Item>

          <Form.Item
            label="Upload policy document or enter URL to policy page"
            className="!mb-0"
          >
            <Flex gap={8} align="start">
              <Select
                aria-label="Policy URLs"
                mode="tags"
                className="flex-1"
                placeholder="https://company.com/privacy"
                value={policyUrls}
                onChange={setPolicyUrls}
                tokenSeparators={[" "]}
                suffixIcon={null}
                open={false}
              />
              <Upload
                accept=".pdf,.docx"
                multiple
                beforeUpload={() => false}
                onChange={handleFileChange}
              >
                <Button
                  aria-label="Upload policy document"
                  icon={<Icons.Upload size={16} />}
                >
                  Upload document
                </Button>
              </Upload>
            </Flex>
          </Form.Item>
        </Form>
      )}
    </Modal>
  );
};

export default PolicySettingsModal;
