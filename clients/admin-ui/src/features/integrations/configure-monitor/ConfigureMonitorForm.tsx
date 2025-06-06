import { format, parseISO } from "date-fns";
import { AntButton as Button, VStack } from "fidesui";
import { Form, Formik } from "formik";
import { useRouter } from "next/router";
import * as Yup from "yup";

import { ControlledSelect } from "~/features/common/form/ControlledSelect";
import {
  CustomDateTimeInput,
  CustomTextInput,
} from "~/features/common/form/inputs";
import { enumToOptions } from "~/features/common/helpers";
import { SharedConfigSelect } from "~/features/integrations/configure-monitor/SharedConfigSelect";
import {
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

    const payload: EditableMonitorConfig = isEditing
      ? {
          ...monitor,
          ...executionInfo,
          name: values.name,
          shared_config_id: values.shared_config_id,
        }
      : {
          ...executionInfo,
          name: values.name,
          shared_config_id: values.shared_config_id,
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
    shared_config_id: monitor?.shared_config_id ?? undefined,
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
