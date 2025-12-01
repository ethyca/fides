import type { Dayjs } from "dayjs";
import dayjs from "dayjs";
import {
  AntButton as Button,
  AntDatePicker as DatePicker,
  AntForm as Form,
  AntInput as Input,
  AntSelect as Select,
  AntSwitch as Switch,
} from "fidesui";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

import { useFeatures } from "~/features/common/features/features.slice";
import { enumToOptions } from "~/features/common/helpers";
import { useGetConfigurationSettingsQuery } from "~/features/config-settings/config-settings.slice";
import {
  ClassifyLlmPromptTemplateOptions,
  ConnectionSystemTypeMap,
  ConnectionType,
  EditableMonitorConfig,
  MonitorConfig,
  MonitorFrequency,
} from "~/types/api";

import { START_TIME_TOOLTIP_COPY } from "./ConfigureWebsiteMonitorForm";
import { FormikSharedConfigSelect } from "./FormikSharedConfigSelect";

interface MonitorConfigFormValues {
  name: string;
  execution_frequency?: MonitorFrequency;
  execution_start_date: Dayjs;
  shared_config_id?: string;
  use_llm_classifier: boolean;
  llm_model_override?: string;
  prompt_template?: ClassifyLlmPromptTemplateOptions;
  content_classification_enabled?: boolean;
}

const DEFAULT_CLASSIFIER_PARAMS = {
  num_samples: 25,
  num_threads: 1,
} as const;

const getClassifyParams = (
  isEditing: boolean,
  monitor: MonitorConfig | undefined,
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
  isSubmitting,
  databasesAvailable,
  onClose,
  onAdvance,
  onSubmit,
}: {
  monitor?: MonitorConfig;
  integrationOption: ConnectionSystemTypeMap;
  isSubmitting?: boolean;
  databasesAvailable?: boolean;
  onClose: () => void;
  onAdvance: (monitor: MonitorConfig) => void;
  onSubmit: (monitor: MonitorConfig) => void;
}) => {
  const isEditing = !!monitor;
  const { flags } = useFeatures();

  /**
   * Feature flag for LLM classifier functionality within action center.
   * Note: Action center can exist for web monitoring without this feature.
   * This flag specifically gates the LLM-based classification capabilities.
   */
  const llmClassifierFeatureEnabled = !!flags.heliosV2;

  const { data: appConfig } = useGetConfigurationSettingsQuery(
    {
      api_set: false,
    },
    { skip: !llmClassifierFeatureEnabled },
  );

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
            execution_start_date: values.execution_start_date.toISOString(),
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
        }
      : {
          ...executionInfo,
          name: values.name,
          shared_config_id: values.shared_config_id,
          connection_config_key: integrationId!,
          classify_params: classifyParams,
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

  const [form] = Form.useForm<MonitorConfigFormValues>();
  const [submittable, setSubmittable] = useState(false);
  const formValues = Form.useWatch([], form);

  useEffect(() => {
    form
      .validateFields({ validateOnly: true })
      .then(() => setSubmittable(true))
      .catch(() => setSubmittable(false));
  }, [form, formValues]);

  const initialValues = {
    name: monitor?.name,
    shared_config_id: monitor?.shared_config_id,
    execution_start_date: dayjs(monitor?.execution_start_date),
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
  } as const;

  return (
    <Form
      form={form}
      onFinish={handleNextClicked}
      className="pt-4"
      layout="vertical"
      validateTrigger="onChange"
      initialValues={initialValues}
    >
      <Form.Item
        label="Name"
        name="name"
        rules={[{ required: true, message: "Please enter a name" }]}
      >
        <Input data-testid="input-name" />
      </Form.Item>
      <Form.Item
        label="Automatic execution frequency"
        name="execution_frequency"
        tooltip="Interval to run the monitor automatically after the start date"
      >
        <Select
          aria-label="Select Automatic execution frequency"
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
      {llmClassifierFeatureEnabled && (
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
