import type { UploadFile } from "fidesui";
import {
  Button,
  Col,
  Flex,
  Form,
  Icons,
  Row,
  Select,
  Spin,
  Text,
  Upload,
  useMessage,
} from "fidesui";
import { useMemo, useState } from "react";

import { useFlags } from "~/features/common/features";

import { useGetLocationsRegulationsQuery } from "../locations/locations.slice";
import {
  useGeneratePoliciesMutation,
  useGetOnboardingDataUsesQuery,
} from "./access-policies.slice";
import { INDUSTRY_OPTIONS } from "./constants";
import DataUseCard from "./DataUseCard";
import { OnboardingFormState } from "./types";

const INITIAL_STATE: OnboardingFormState = {
  industry: null,
  geographies: [],
  selectedDataUses: [],
};

const OnboardingForm = () => {
  const { flags } = useFlags();
  const [formState, setFormState] =
    useState<OnboardingFormState>(INITIAL_STATE);
  const message = useMessage();
  const [policyUrls, setPolicyUrls] = useState<string[]>([]);
  const [policyFiles, setPolicyFiles] = useState<File[]>([]);
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

  const canGenerate = !!formState.industry && formState.geographies.length > 0;

  const { data, isLoading, isFetching } = useGetOnboardingDataUsesQuery(
    { industry: formState.industry!, geographies: formState.geographies },
    { skip: !formState.industry || formState.geographies.length === 0 },
  );

  const dataUses = data?.items ?? [];
  const isDataUsesLoading = isLoading || isFetching;

  const handleToggleDataUse = (id: string) => {
    setFormState((prev) => ({
      ...prev,
      selectedDataUses: prev.selectedDataUses.includes(id)
        ? prev.selectedDataUses.filter((d) => d !== id)
        : [...prev.selectedDataUses, id],
    }));
  };

  const handleFileChange = (info: { fileList: UploadFile[] }) => {
    setPolicyFiles(
      info.fileList
        .map((f) => f.originFileObj as File | undefined)
        .filter((f): f is File => !!f),
    );
  };

  const handleSubmit = async () => {
    if (!formState.industry || formState.geographies.length === 0) {
      return;
    }
    const formData = new FormData();
    formData.append("industry", formState.industry);
    formState.geographies.forEach((g) => formData.append("geographies", g));
    formState.selectedDataUses.forEach((d) =>
      formData.append("selected_data_uses", d),
    );
    policyUrls.forEach((u) => formData.append("policy_urls", u));
    policyFiles.forEach((f) => formData.append("files", f));
    try {
      await generatePolicies(formData).unwrap();
      message.success("Policies generated successfully");
    } catch {
      message.error("Failed to generate policies");
    }
  };

  const renderDataUseCards = () => {
    if (!formState.industry || formState.geographies.length === 0) {
      return (
        <div className="rounded-lg border border-dashed border-gray-300 px-6 py-10 text-center">
          <Text type="secondary">
            Select a business vertical and geography to see common data uses.
          </Text>
        </div>
      );
    }

    if (isDataUsesLoading) {
      return (
        <div className="flex justify-center py-8">
          <Spin />
        </div>
      );
    }

    return (
      <Row gutter={[12, 12]}>
        {dataUses.map((dataUseId) => (
          <Col key={dataUseId} xs={24} md={12}>
            <DataUseCard
              dataUseId={dataUseId}
              isSelected={formState.selectedDataUses.includes(dataUseId)}
              onClick={() => handleToggleDataUse(dataUseId)}
            />
          </Col>
        ))}
      </Row>
    );
  };

  return (
    <div className="max-w-3xl">
      <div className="rounded-lg border border-dashed border-gray-300 p-6">
        <div className="mb-6">
          <Text strong>Configure your policies</Text>
          <div className="mt-1">
            <Text type="secondary">
              Tell us about your organization and Fides will generate access
              policies tailored to your industry and regulatory environment.
            </Text>
          </div>
        </div>
        <Form layout="vertical">
          <Flex vertical gap={24}>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  label="Business vertical / industry"
                  required
                  htmlFor="industry-select"
                  className="!mb-0"
                >
                  <Select
                    id="industry-select"
                    aria-label="Business vertical / industry"
                    className="w-full"
                    placeholder="Select industry"
                    value={formState.industry}
                    onChange={(value) =>
                      setFormState((prev) => ({
                        ...prev,
                        industry: value,
                        selectedDataUses: [],
                      }))
                    }
                    options={INDUSTRY_OPTIONS}
                    allowClear
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  label="Geography"
                  required
                  htmlFor="geography-select"
                  className="!mb-0"
                >
                  <Select
                    id="geography-select"
                    aria-label="Geography"
                    className="w-full"
                    mode="multiple"
                    placeholder="Select geographies"
                    loading={isLocationsLoading}
                    value={formState.geographies}
                    onChange={(value) =>
                      setFormState((prev) => ({
                        ...prev,
                        geographies: value,
                        selectedDataUses: [],
                      }))
                    }
                    options={geographyOptions}
                    allowClear
                  />
                </Form.Item>
              </Col>
            </Row>

            <div>
              <Form.Item label="Common data uses" className="!mb-2">
                <Text type="secondary" size="sm">
                  Select the data use categories most relevant to your
                  organization. This helps Fides prioritize scanning and
                  generate more targeted access policies.
                </Text>
              </Form.Item>
              {renderDataUseCards()}
            </div>

            {flags.alphaPrivacyDocUpload && (
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
                      Upload
                    </Button>
                  </Upload>
                </Flex>
              </Form.Item>
            )}

            <div>
              <Button
                type="primary"
                onClick={handleSubmit}
                disabled={!canGenerate}
                loading={isGenerating}
              >
                Generate policies
              </Button>
            </div>
          </Flex>
        </Form>
      </div>
    </div>
  );
};

export default OnboardingForm;
