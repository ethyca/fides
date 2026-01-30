import { skipToken } from "@reduxjs/toolkit/query";
import type { Dayjs } from "dayjs";
import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";
import { Button, DatePicker, Form, Input, Select, Switch } from "fidesui";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

import { useFeatures } from "~/features/common/features/features.slice";
import { enumToOptions } from "~/features/common/helpers";
import { formatUser } from "~/features/common/utils";
import { useGetConfigurationSettingsQuery } from "~/features/config-settings/config-settings.slice";
import {
  getMonitorType,
  MONITOR_TYPES,
} from "~/features/data-discovery-and-detection/action-center/utils/getMonitorType";
import { useGetSystemByFidesKeyQuery } from "~/features/system";
import { useGetAllUsersQuery } from "~/features/user-management";
import {
  ClassifyLlmPromptTemplateOptions,
  ConnectionSystemTypeMap,
  ConnectionType,
  EditableMonitorConfig,
  MonitorFrequency,
} from "~/types/api";

import { START_TIME_TOOLTIP_COPY } from "./ConfigureWebsiteMonitorForm";
import { FormikSharedConfigSelect } from "./FormikSharedConfigSelect";

dayjs.extend(utc);

interface MonitorConfigFormValues {
  name: string;
  execution_frequency?: MonitorFrequency;
  execution_start_date: Dayjs;
  shared_config_id?: string;
  use_llm_classifier: boolean;
  llm_model_override?: string;
  prompt_template?: ClassifyLlmPromptTemplateOptions;
  content_classification_enabled?: boolean;
  stewards?: string[];
}

const DEFAULT_CLASSIFIER_PARAMS = {
  num_samples: 25,
  num_threads: 1,
} as const;

const getClassifyParams = (
  isEditing: boolean,
  monitor: EditableMonitorConfig | undefined,
  values: MonitorConfigFormValues,
) => {
  const baseParams = isEditing
    ? {
        ...monitor?.classify_params,
      }
    : DEFAULT_CLASSIFIER_PARAMS;

  if (values.use_llm_classifier) {
    return {
      ...baseParams,
      context_classifier: "llm",
      ...(values.llm_model_override && {
        llm_model_override: values.llm_model_override,
      }),
      ...(values.prompt_template && {
        prompt_template: values.prompt_template,
      }),
      content_classification_enabled: false, // for now, content classification is always disabled for LLM classification
    };
  }

  return {
    ...baseParams,
    context_classifier: undefined,
    llm_model_override: undefined,
    prompt_template: undefined,
    content_classification_enabled: undefined,
  };
};

const ConfigureMonitorForm = ({
  monitor,
  integrationOption,
  integrationSystem,
  isSubmitting,
  databasesAvailable,
  onClose,
  onAdvance,
  onSubmit,
}: {
  monitor?: EditableMonitorConfig;
  integrationOption: ConnectionSystemTypeMap;
  integrationSystem?: string | null;
  isSubmitting?: boolean;
  databasesAvailable?: boolean;
  onClose: () => void;
  onAdvance: (monitor: EditableMonitorConfig) => void;
  onSubmit: (monitor: EditableMonitorConfig) => void;
}) => {
  const isEditing = !!monitor;
  const { flags } = useFeatures();

  /**
   * Feature flag for LLM classifier functionality within action center.
   * Note: Action center can exist for web monitoring without this feature.
   * This flag specifically gates the LLM-based classification capabilities.
   */
  const llmClassifierFeatureEnabled = !!flags.heliosV2;

  const isInfrastructureMonitor =
    getMonitorType(integrationOption.identifier as ConnectionType) ===
    MONITOR_TYPES.INFRASTRUCTURE;

  /**
   * Show the LLM classifier option if the feature is enabled and the monitor is not an infrastructure monitor.
   * Infrastructure monitors (e.g., Okta) don't use classification.
   */
  const showLLMOption = llmClassifierFeatureEnabled && !isInfrastructureMonitor;

  const { data: appConfig } = useGetConfigurationSettingsQuery(
    {
      api_set: false,
    },
    { skip: !llmClassifierFeatureEnabled },
  );

  const [form] = Form.useForm<MonitorConfigFormValues>();
  const { data: systemData, isLoading: isLoadingSystem } =
    useGetSystemByFidesKeyQuery(integrationSystem || skipToken);

  /**
   * Server-side LLM classifier capability.
   * This determines if the backend supports LLM-based classification for monitors.
   */
  const serverSupportsLlmClassifier =
    !!appConfig?.detection_discovery?.llm_classifier_enabled;

  const router = useRouter();
  const integrationId = Array.isArray(router.query.id)
    ? router.query.id[0]
    : router.query.id;

  const handleNextClicked = (values: MonitorConfigFormValues) => {
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

    const classifyParams = getClassifyParams(isEditing, monitor, values);
    const payload: EditableMonitorConfig = isEditing
      ? {
          ...monitor,
          ...executionInfo,
          name: values.name,
          shared_config_id: values.shared_config_id,
          classify_params: classifyParams,
          stewards: values.stewards,
        }
      : {
          ...executionInfo,
          name: values.name,
          shared_config_id: values.shared_config_id,
          connection_config_key: integrationId!,
          classify_params: classifyParams,
          stewards: values.stewards,
        };

    if (integrationOption.identifier === ConnectionType.DYNAMODB) {
      payload.datasource_params = {
        single_dataset: false,
      };
    }
    if (databasesAvailable) {
      onAdvance(payload);
    } else {
      onSubmit(payload);
    }
  };

  /**
   * Check if this monitor is currently configured to use LLM classification.
   * This is independent of whether the server supports it or the feature is enabled.
   */
  const monitorUsesLlmClassifier =
    monitor?.classify_params?.context_classifier === "llm";

  const [submittable, setSubmittable] = useState(false);
  const formValues = Form.useWatch([], form);

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

  // TODO: build better pattern for async form initialization
  useEffect(() => {
    form.resetFields();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoadingSystem]);

  useEffect(() => {
    form
      .validateFields({ validateOnly: true })
      .then(() => setSubmittable(true))
      .catch(() => setSubmittable(false));
  }, [form, formValues]);

  const initialValues = {
    name: monitor?.name,
    shared_config_id: monitor?.shared_config_id,
    execution_start_date: dayjs(monitor?.execution_start_date ?? undefined),
    execution_frequency:
      monitor?.execution_frequency ?? MonitorFrequency.MONTHLY,
    use_llm_classifier: monitorUsesLlmClassifier && serverSupportsLlmClassifier,
    llm_model_override: monitorUsesLlmClassifier
      ? (monitor?.classify_params?.llm_model_override ?? undefined)
      : undefined,
    prompt_template: monitorUsesLlmClassifier
      ? (monitor?.classify_params?.prompt_template ?? undefined)
      : undefined,
    content_classification_enabled: !monitorUsesLlmClassifier
      ? monitor?.classify_params?.content_classification_enabled
      : undefined, // for now, content classification is always disabled for LLM classification
    stewards:
      monitor?.stewards ?? systemData?.data_stewards?.map(({ id }) => id),
  } as const;

  return (
    <Form
      form={form}
      onFinish={handleNextClicked}
      className="pt-4"
      layout="vertical"
      validateTrigger="onChange"
      initialValues={initialValues}
      disabled={isLoadingSystem} // TODO: establish better pattern and styles for async form initialization
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
        label="Automatic execution frequency"
        name="execution_frequency"
        tooltip="Interval to run the monitor automatically after the start date"
      >
        <Select
          aria-label="Select automatic execution frequency"
          data-testid="controlled-select-execution_frequency"
          options={enumToOptions(MonitorFrequency)}
        />
      </Form.Item>
      <FormikSharedConfigSelect
        name="shared_config_id"
        onChange={(value) => form.setFieldValue("shared_config_id", value)}
        value={form.getFieldValue("shared_config_id")}
      />
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
      {showLLMOption && (
        <>
          <Form.Item
            name="use_llm_classifier"
            label="Use LLM classifier"
            tooltip={
              !serverSupportsLlmClassifier
                ? "LLM classifier is currently disabled for this server. Contact Ethyca support to learn more."
                : undefined
            }
            valuePropName="checked"
          >
            <Switch
              data-testid="input-use_llm_classifier"
              disabled={!serverSupportsLlmClassifier}
              checked={form.getFieldValue("use_llm_classifier")}
            />
          </Form.Item>
          {form.getFieldValue("use_llm_classifier") && (
            <Form.Item
              name="llm_model_override"
              label="Model override"
              tooltip="Optionally specify a custom model to use for LLM classification"
            >
              <Input data-testid="input-llm_model_override" />
            </Form.Item>
          )}
        </>
      )}
      <div className="flex w-full justify-between">
        <Button
          onClick={() => {
            form.resetFields();
            onClose();
          }}
        >
          Cancel
        </Button>
        <Button
          htmlType="submit"
          type="primary"
          disabled={!submittable}
          loading={isSubmitting}
          data-testid="next-btn"
        >
          {databasesAvailable ? "Next" : "Save"}
        </Button>
      </div>
    </Form>
  );
};

export default ConfigureMonitorForm;
