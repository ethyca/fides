import { format, parseISO } from "date-fns";
import { AntButton as Button, VStack } from "fidesui";
import { Form, Formik } from "formik";
import { useRouter } from "next/router";
import * as Yup from "yup";

import { useFeatures } from "~/features/common/features/features.slice";
import { ControlledSelect } from "~/features/common/form/ControlledSelect";
import {
  CustomDateTimeInput,
  CustomSwitch,
  CustomTextInput,
} from "~/features/common/form/inputs";
import { enumToOptions } from "~/features/common/helpers";
import { useGetConfigurationSettingsQuery } from "~/features/config-settings/config-settings.slice";
import { SharedConfigSelect } from "~/features/integrations/configure-monitor/SharedConfigSelect";
import {
  ClassifyLlmPromptTemplateOptions,
  ConnectionSystemTypeMap,
  ConnectionType,
  EditableMonitorConfig,
  MonitorConfig,
  MonitorFrequency,
} from "~/types/api";

interface MonitorConfigFormValues {
  name: string;
  execution_frequency?: MonitorFrequency;
  execution_start_date: string;
  shared_config_id?: string;
  use_llm_classifier: boolean;
  llm_model_override?: string;
  prompt_template?: ClassifyLlmPromptTemplateOptions;
  content_classification_enabled?: boolean;
}

const DEFAULT_CLASSIFIER_PARAMS = {
  num_samples: 25,
  num_threads: 1,
};

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
  const llmClassifierFeatureEnabled = !!flags.llmClassifier;

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

  const validationSchema = Yup.object().shape({
    name: Yup.string().required().label("Name"),
    execution_frequency: Yup.string().nullable().label("Execution frequency"),
    execution_start_date: Yup.date().nullable().label("Execution start date"),
  });

  const handleNextClicked = (values: MonitorConfigFormValues) => {
    const executionInfo =
      values.execution_frequency !== MonitorFrequency.NOT_SCHEDULED
        ? {
            execution_frequency: values.execution_frequency,
            execution_start_date: new Date(
              values.execution_start_date,
            ).toISOString(),
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

  const initialDate = monitor?.execution_start_date
    ? parseISO(monitor.execution_start_date)
    : Date.now();

  /**
   * Check if this monitor is currently configured to use LLM classification.
   * This is independent of whether the server supports it or the feature is enabled.
   */
  const monitorUsesLlmClassifier =
    monitor?.classify_params?.context_classifier === "llm";

  const initialValues = {
    name: monitor?.name ?? "",
    shared_config_id: monitor?.shared_config_id ?? undefined,
    execution_start_date: format(initialDate, "yyyy-MM-dd'T'HH:mm"),
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
      ? (monitor?.classify_params?.content_classification_enabled ?? undefined)
      : undefined, // for now, content classification is always disabled for LLM classification
  };

  const frequencyOptions = enumToOptions(MonitorFrequency);

  return (
    <Formik
      initialValues={initialValues}
      enableReinitialize
      onSubmit={handleNextClicked}
      validationSchema={validationSchema}
    >
      {({ values, isValid, resetForm }) => (
        <Form>
          <VStack alignItems="start" spacing={6} mt={4}>
            <CustomTextInput
              name="name"
              id="name"
              label="Name"
              isRequired
              variant="stacked"
            />
            <ControlledSelect
              name="execution_frequency"
              id="execution_frequency"
              tooltip="Interval to run the monitor automatically after the start date"
              options={frequencyOptions}
              label="Automatic execution frequency"
              layout="stacked"
            />
            <SharedConfigSelect name="shared_config_id" id="shared_config_id" />
            <CustomDateTimeInput
              name="execution_start_date"
              label="Automatic execution start time"
              disabled={
                values.execution_frequency === MonitorFrequency.NOT_SCHEDULED
              }
              id="execution_start_date"
            />
            {llmClassifierFeatureEnabled && (
              <>
                <CustomSwitch
                  name="use_llm_classifier"
                  id="use_llm_classifier"
                  label="Use LLM classifier"
                  variant="stacked"
                  isDisabled={!serverSupportsLlmClassifier}
                  tooltip={
                    !serverSupportsLlmClassifier
                      ? "LLM classifier is currently disabled for this server. Contact Ethyca support to learn more."
                      : undefined
                  }
                />
                {values.use_llm_classifier && (
                  <CustomTextInput
                    name="llm_model_override"
                    id="llm_model_override"
                    label="Model override"
                    variant="stacked"
                    tooltip="Optionally specify a custom model to use for LLM classification"
                  />
                )}
              </>
            )}
            <div className="flex w-full justify-between">
              <Button
                onClick={() => {
                  resetForm();
                  onClose();
                }}
              >
                Cancel
              </Button>
              <Button
                htmlType="submit"
                type="primary"
                disabled={!isValid}
                loading={isSubmitting}
                data-testid="next-btn"
              >
                {databasesAvailable ? "Next" : "Save"}
              </Button>
            </div>
          </VStack>
        </Form>
      )}
    </Formik>
  );
};

export default ConfigureMonitorForm;
