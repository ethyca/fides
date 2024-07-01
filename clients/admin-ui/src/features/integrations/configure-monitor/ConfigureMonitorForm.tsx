import { format, parseISO } from "date-fns";
import { Button, ButtonGroup, VStack } from "fidesui";
import { Form, Formik } from "formik";
import { useRouter } from "next/router";
import * as Yup from "yup";

import {
  CustomDateTimeInput,
  CustomSelect,
  CustomTextInput,
} from "~/features/common/form/inputs";
import useQueryResultToast from "~/features/common/form/useQueryResultToast";
import { enumToOptions, isErrorResult } from "~/features/common/helpers";
import { usePutDiscoveryMonitorMutation } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import {
  ConnectionSystemTypeMap,
  ConnectionType,
  MonitorConfig,
  MonitorFrequency,
} from "~/types/api";

const NOT_SCHEDULED = "Not scheduled";

type FrequencyOption = MonitorFrequency | typeof NOT_SCHEDULED;

interface MonitorConfigFormValues {
  name: string;
  execution_frequency?: FrequencyOption;
  execution_start_date: string;
}

const ConfigureMonitorForm = ({
  monitor,
  integrationOption,
  onClose,
  onAdvance,
}: {
  monitor?: MonitorConfig;
  integrationOption: ConnectionSystemTypeMap;
  onClose: () => void;
  onAdvance: (monitor: MonitorConfig) => void;
}) => {
  const isEditing = !!monitor;

  const { query } = useRouter();
  const integrationId = Array.isArray(query.id) ? query.id[0] : query.id;

  const validationSchema = Yup.object().shape({
    name: Yup.string().required().label("Name"),
    execution_frequency: Yup.string().nullable().label("Execution frequency"),
    execution_start_date: Yup.date().nullable().label("Execution start date"),
  });

  const [putMonitorMutationTrigger, { isLoading }] =
    usePutDiscoveryMonitorMutation();

  const { toastResult } = useQueryResultToast({
    defaultSuccessMsg: `Monitor ${
      isEditing ? "updated" : "created"
    } successfully`,
    defaultErrorMsg: `A problem occurred while ${
      isEditing ? "updating" : "creating"
    } this monitor`,
  });

  const handleSubmit = async (values: MonitorConfigFormValues) => {
    const executionInfo =
      values.execution_frequency !== NOT_SCHEDULED
        ? {
            execution_frequency: values.execution_frequency,
            execution_start_date: new Date(
              values.execution_start_date
            ).toISOString(),
          }
        : { execution_frequency: undefined, execution_start_date: undefined };

    const payload: MonitorConfig = isEditing
      ? {
          ...monitor,
          ...executionInfo,
          name: values.name,
        }
      : {
          ...executionInfo,
          name: values.name,
          connection_config_key: integrationId!,
          classify_params: {
            num_samples: 25,
            num_threads: 1,
          },
        };

    if (integrationOption.identifier === ConnectionType.DYNAMODB) {
      payload.datasource_params = {
        single_dataset: false,
      };
    }
    const result = await putMonitorMutationTrigger(payload);
    toastResult(result);
    if (!isErrorResult(result)) {
      onAdvance(result.data);
    }
  };

  const handleNextClicked = (
    values: MonitorConfigFormValues,
    isDirty: boolean
  ) => {
    if (isDirty) {
      handleSubmit(values);
    } else {
      onAdvance(monitor!);
    }
  };

  const initialDate = monitor?.execution_start_date
    ? parseISO(monitor.execution_start_date)
    : Date.now();

  const initialValues = {
    name: monitor?.name ?? "",
    execution_start_date: format(initialDate, "yyyy-MM-dd'T'HH:mm"),
    execution_frequency:
      monitor?.execution_frequency ?? (NOT_SCHEDULED as FrequencyOption),
  };

  const frequencyOptions = [
    { label: NOT_SCHEDULED, value: NOT_SCHEDULED },
    ...enumToOptions(MonitorFrequency),
  ];

  return (
    <Formik
      initialValues={initialValues}
      enableReinitialize
      onSubmit={handleSubmit}
      validationSchema={validationSchema}
    >
      {({ values, dirty, isValid, resetForm }) => (
        <Form>
          <VStack alignItems="start" spacing={6} mt={4}>
            <CustomTextInput
              name="name"
              id="name"
              label="Name"
              isRequired
              variant="stacked"
            />
            <CustomSelect
              name="execution_frequency"
              id="execution_frequency"
              tooltip="Interval to run the monitor automatically after the start date"
              options={frequencyOptions}
              label="Automatic execution frequency"
              variant="stacked"
            />
            <CustomDateTimeInput
              name="execution_start_date"
              label="Automatic execution start time"
              disabled={values.execution_frequency === NOT_SCHEDULED}
              id="execution_start_date"
            />
            <ButtonGroup size="sm" w="full" justifyContent="space-between">
              <Button
                variant="outline"
                onClick={() => {
                  resetForm();
                  onClose();
                }}
              >
                Cancel
              </Button>
              <Button
                onClick={() => handleNextClicked(values, dirty)}
                variant="primary"
                isDisabled={!isValid}
                isLoading={isLoading}
                data-testid="next-btn"
              >
                Next
              </Button>
            </ButtonGroup>
          </VStack>
        </Form>
      )}
    </Formik>
  );
};

export default ConfigureMonitorForm;
