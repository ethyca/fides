import { format, parseISO } from "date-fns";
import { AntButton, VStack } from "fidesui";
import { Form, Formik } from "formik";
import { useRouter } from "next/router";
import * as Yup from "yup";

import {
  CustomDateTimeInput,
  CustomSelect,
  CustomTextInput,
} from "~/features/common/form/inputs";
import { enumToOptions } from "~/features/common/helpers";
import {
  ConnectionSystemTypeMap,
  ConnectionType,
  MonitorConfig,
  MonitorFrequency,
} from "~/types/api";

interface MonitorConfigFormValues {
  name: string;
  execution_frequency?: MonitorFrequency;
  execution_start_date: string;
}

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

  const { query } = useRouter();
  const integrationId = Array.isArray(query.id) ? query.id[0] : query.id;

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
    if (databasesAvailable) {
      onAdvance(payload);
    } else {
      onSubmit(payload);
    }
  };

  const initialDate = monitor?.execution_start_date
    ? parseISO(monitor.execution_start_date)
    : Date.now();

  const initialValues = {
    name: monitor?.name ?? "",
    execution_start_date: format(initialDate, "yyyy-MM-dd'T'HH:mm"),
    execution_frequency:
      monitor?.execution_frequency ?? MonitorFrequency.MONTHLY,
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
              disabled={
                values.execution_frequency === MonitorFrequency.NOT_SCHEDULED
              }
              id="execution_start_date"
            />
            <div className="flex w-full justify-between">
              <AntButton
                onClick={() => {
                  resetForm();
                  onClose();
                }}
              >
                Cancel
              </AntButton>
              <AntButton
                htmlType="submit"
                type="primary"
                disabled={!isValid}
                loading={isSubmitting}
                data-testid="next-btn"
              >
                {databasesAvailable ? "Next" : "Save"}
              </AntButton>
            </div>
          </VStack>
        </Form>
      )}
    </Formik>
  );
};

export default ConfigureMonitorForm;
