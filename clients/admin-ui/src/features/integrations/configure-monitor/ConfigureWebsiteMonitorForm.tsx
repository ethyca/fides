import { skipToken } from "@reduxjs/toolkit/query";
import type { Dayjs } from "dayjs";
import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";
import {
  AntTooltip as Tooltip,
  Button,
  DatePicker,
  Flex,
  Form,
  Input,
  isoCodesToOptions,
  LocationSelect,
  Select,
  Text,
} from "fidesui";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

import { useFlags } from "~/features/common/features/features.slice";
import FormInfoBox from "~/features/common/modals/FormInfoBox";
import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import { formatUser } from "~/features/common/utils";
import { useGetConfigurationSettingsQuery } from "~/features/config-settings/config-settings.slice";
import { useGetOnlyCountryLocationsQuery } from "~/features/locations/locations.slice";
import { getSelectedRegionIds } from "~/features/privacy-experience/form/helpers";
import { useGetSystemByFidesKeyQuery } from "~/features/system";
import { useGetAllUsersQuery } from "~/features/user-management";
import {
  EditableMonitorConfig,
  MonitorFrequency,
  WebsiteMonitorParams,
} from "~/types/api";

import { FormikSharedConfigSelect } from "./FormikSharedConfigSelect";

dayjs.extend(utc);

interface WebsiteMonitorConfig
  extends Omit<EditableMonitorConfig, "datasource_params"> {
  datasource_params?: WebsiteMonitorParams;
  url: string;
  llm_model_override?: string;
}

interface WebsiteMonitorConfigFormValues {
  name: string;
  url: string;
  execution_frequency?: MonitorFrequency;
  datasource_params?: WebsiteMonitorParams;
  execution_start_date: Dayjs;
  shared_config_id?: string;
  stewards?: string[];
  llm_model_override?: string;
}
const FORM_COPY = `This monitor allows you to simulate and verify user consent actions, such as 'accept,' 'reject,' or 'opt-out,' on consent experiences. For each detected activity, the monitor will record whether it occurred before or after the configured user actions, ensuring compliance with user consent choices.`;

const REGIONS_TOOLTIP_COPY = `Specify the region(s) to include in the scan. The monitor will scan the same URL across these locations to identify tracking technologies, such as cookies served by ad tech vendors.`;

export const START_TIME_TOOLTIP_COPY = `Set the start time for the scan. For optimal performance and minimal disruption, schedule scans during periods of low traffic.`;

const ConfigureWebsiteMonitorForm = ({
  monitor,
  url,
  integrationSystem,
  onClose,
  onSubmit,
}: {
  monitor?: EditableMonitorConfig;
  url: string;
  integrationSystem?: string | null;
  onClose: () => void;
  onSubmit: (values: EditableMonitorConfig) => Promise<void>;
}) => {
  const [form] = Form.useForm<WebsiteMonitorConfigFormValues>();
  const [submittable, setSubmittable] = useState(false);
  const formValues = Form.useWatch([], form);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();
  const { flags } = useFlags();

  // Feature flag for LLM classification in website monitors
  const llmClassifierFeatureEnabled = !!flags.alphaWebMonitorLlmClassification;

  const { data: appConfig } = useGetConfigurationSettingsQuery(
    { api_set: false },
    { skip: !llmClassifierFeatureEnabled },
  );

  // Server-side LLM classifier capability
  const serverSupportsLlmClassifier =
    !!appConfig?.detection_discovery?.llm_classifier_enabled;

  const integrationId = Array.isArray(router.query.id)
    ? router.query.id[0]
    : (router.query.id as string);

  const { data: locationRegulationResponse, isLoading: locationsLoading } =
    useGetOnlyCountryLocationsQuery();

  const { data: systemData, isLoading: isLoadingSystem } =
    useGetSystemByFidesKeyQuery(integrationSystem || skipToken);

  const { data: eligibleUsersData } = useGetAllUsersQuery({
    page: 1,
    size: 100,
    include_external: false,
    exclude_approvers: true,
  });

  const dataStewardOptions = (eligibleUsersData?.items || []).map((user) => ({
    label: formatUser(user),
    value: user.id,
  }));

  const allSelectedRegions = [
    ...getSelectedRegionIds(locationRegulationResponse?.locations ?? []),
    ...getSelectedRegionIds(locationRegulationResponse?.location_groups ?? []),
  ];

  const regionOptions = allSelectedRegions.map((region) => ({
    value: region,
    label: PRIVACY_NOTICE_REGION_RECORD[region],
  }));

  const initialValues: WebsiteMonitorConfigFormValues = {
    name: monitor?.name || "",
    shared_config_id: monitor?.shared_config_id ?? undefined,
    execution_frequency:
      monitor?.execution_frequency || MonitorFrequency.NOT_SCHEDULED,
    execution_start_date: dayjs(monitor?.execution_start_date ?? undefined),
    url,
    datasource_params: (monitor?.datasource_params as WebsiteMonitorParams) ?? {
      locations: [],
      exclude_domains: [],
    },
stewards:
      monitor?.stewards ?? systemData?.data_stewards?.map(({ id }) => id),
    llm_model_override: monitor?.classify_params?.llm_model_override ?? "",
  };

  const handleSubmit = async (values: WebsiteMonitorConfigFormValues) => {
    setIsSubmitting(true);
    const executionInfo =
      values.execution_frequency !== MonitorFrequency.NOT_SCHEDULED
        ? {
            execution_frequency: values.execution_frequency,
            execution_start_date: values.execution_start_date
              .utc()
              .format("YYYY-MM-DD[T]HH:mm:ss[Z]"),
          }
        : {
            execution_frequency: MonitorFrequency.NOT_SCHEDULED,
            execution_start_date: undefined,
          };

    // Build classify_params with llm_model_override if provided
    const classifyParams = {
      ...(monitor?.classify_params || {}),
      ...(values.llm_model_override
        ? { llm_model_override: values.llm_model_override }
        : { llm_model_override: undefined }),
    };

    const payload: WebsiteMonitorConfig = {
      ...monitor,
      ...values,
      ...executionInfo,
      key: monitor?.key,
      classify_params: classifyParams,
      datasource_params: values.datasource_params || {},
      connection_config_key: integrationId,
    };
    onSubmit(payload);
  };

  useEffect(() => {
    form
      .validateFields({ validateOnly: true })
      .then(() => setSubmittable(true))
      .catch(() => setSubmittable(false));
  }, [form, formValues]);

  // TODO: build better pattern for async form initialization
  useEffect(() => {
    form.resetFields();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoadingSystem]);

  return (
    <Flex vertical className="pt-4">
      <FormInfoBox>
        <Text>{FORM_COPY}</Text>
      </FormInfoBox>
      <Form
        form={form}
        initialValues={initialValues}
        onFinish={handleSubmit}
        layout="vertical"
      >
        <Form.Item
          label="Name"
          name="name"
          rules={[{ required: true, message: "Please enter a name" }]}
        >
          <Input data-testid="input-name" />
        </Form.Item>
        <Form.Item label="Stewards" name="stewards">
          <Select
            mode="multiple"
            aria-label="Select stewards"
            data-testid="controlled-select-stewards"
            options={dataStewardOptions}
          />
        </Form.Item>
        <Form.Item
          label="Sitemap URL"
          name={["datasource_params", "sitemap_url"]}
          rules={[{ type: "url" }]}
        >
          <Input data-testid="input-datasource_params.sitemap_url" />
        </Form.Item>
        <Form.Item
          label="Exclude domains"
          name={["datasource_params", "exclude_domains"]}
        >
          <Select
            placeholder="Enter domains to exclude"
            aria-label="Domains to exclude"
            data-testid="controlled-select-exclude_domains"
            mode="tags"
            open={false}
            suffixIcon={null}
            options={[]}
          />
        </Form.Item>
        <Form.Item label="URL" name="url">
          <Input data-testid="input-url" disabled />
        </Form.Item>
        <Form.Item
          name={["datasource_params", "locations"]}
          label="Locations"
          id="locations"
          tooltip={REGIONS_TOOLTIP_COPY}
        >
          <LocationSelect
            data-testid="controlled-select-datasource_params.locations"
            loading={locationsLoading}
            mode="multiple"
            options={isoCodesToOptions(
              regionOptions.map((option) => option.value),
            )}
          />
        </Form.Item>
        <FormikSharedConfigSelect
          name="shared_config_id"
          onChange={(value) => form.setFieldValue("shared_config_id", value)}
          value={form.getFieldValue("shared_config_id")}
        />
{llmClassifierFeatureEnabled && (
          <Form.Item
            label={
              <Tooltip
                title={
                  !serverSupportsLlmClassifier
                    ? "LLM classifier is currently disabled for this server. Contact Ethyca support to learn more."
                    : "Optionally specify a custom model to use for LLM classification of website assets"
                }
              >
                <span>LLM model override</span>
              </Tooltip>
            }
            name="llm_model_override"
          >
            <Input
              data-testid="input-llm_model_override"
              placeholder="e.g., openrouter/google/gemini-2.5-flash"
              disabled={!serverSupportsLlmClassifier}
            />
          </Form.Item>
        )}
        <Form.Item
          label="Automatic execution frequency"
          name="execution_frequency"
          tooltip="Interval to run the monitor automatically after the start date"
        >
          <Select
            aria-label="Select automatic execution frequency"
            data-testid="controlled-select-execution_frequency"
            options={[
              MonitorFrequency.MONTHLY,
              MonitorFrequency.QUARTERLY,
              MonitorFrequency.YEARLY,
              MonitorFrequency.NOT_SCHEDULED,
            ].map((frequency) => ({ label: frequency, value: frequency }))}
          />
        </Form.Item>
        <Form.Item
          label="Automatic execution start time"
          name="execution_start_date"
          tooltip={START_TIME_TOOLTIP_COPY}
        >
          <DatePicker
            data-testid="input-execution_start_date"
            disabled={
              form.getFieldValue("execution_frequency") ===
              MonitorFrequency.NOT_SCHEDULED
            }
            showTime
          />
        </Form.Item>
        <Flex gap="small" className="mt-2" justify="stretch">
          <Button
            onClick={() => {
              form.resetFields();
              onClose();
            }}
            block
          >
            Cancel
          </Button>
          <Button
            type="primary"
            htmlType="submit"
            data-testid="save-btn"
            block
            loading={isSubmitting}
            disabled={!submittable}
          >
            Save
          </Button>
        </Flex>
      </Form>
    </Flex>
  );
};

export default ConfigureWebsiteMonitorForm;
