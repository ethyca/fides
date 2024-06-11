import { formatISO } from "date-fns";
import { Button, ButtonGroup, VStack } from "fidesui";
import { Form, Formik } from "formik";
import { useRouter } from "next/router";
import * as Yup from "yup";

import {
  CustomDatePicker,
  CustomSelect,
  CustomTextInput,
} from "~/features/common/form/inputs";
import useQueryResultToast from "~/features/common/form/useQueryResultToast";
import { enumToOptions, isErrorResult } from "~/features/common/helpers";
import { usePutDiscoveryMonitorMutation } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import { MonitorConfig, MonitorFrequency } from "~/types/api";

type FormValues = {
  name: string;
  execution_start_date: string;
  execution_frequency?: MonitorFrequency;
};

const ConfigureMonitorForm = ({
  monitor,
  onClose,
  onAdvance,
}: {
  monitor?: MonitorConfig;
  onClose: () => void;
  onAdvance: (monitor: MonitorConfig) => void;
}) => {
  const isEditing = !!monitor;

  const { query } = useRouter();
  const integrationId = Array.isArray(query.id) ? query.id[0] : query.id;

  const CURRENT_DATE_ISO = formatISO(Date.now(), { representation: "date" });

  const validationSchema = Yup.object().shape({
    name: Yup.string().required().label("Name"),
    execution_start_date: isEditing
      ? Yup.string().nullable()
      : Yup.date()
          .transform((dateString) => new Date(dateString))
          .min(CURRENT_DATE_ISO)
          .label("Execution start date"),
    execution_frequency: Yup.string().required().label("Execution frequency"),
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

  const handleSubmit = async (values: FormValues) => {
    const startDate = new Date(values.execution_start_date);
    startDate.setUTCHours(0, 0, 0);

    const payload: MonitorConfig = isEditing
      ? {
          ...monitor,
          name: values.name,
          execution_frequency: values.execution_frequency,
        }
      : {
          name: values.name,
          connection_config_key: integrationId!,
          execution_frequency: values.execution_frequency,
          execution_start_date: startDate.toISOString(),
          classify_params: {
            num_samples: 25,
            num_threads: 1,
          },
        };

    const result = await putMonitorMutationTrigger(payload);
    toastResult(result);
    if (!isErrorResult(result)) {
      onAdvance(result.data);
    }
  };

  const handleNextClicked = (values: FormValues, isDirty: boolean) => {
    if (isDirty) {
      handleSubmit(values);
    } else {
      onAdvance(monitor!);
    }
  };

  const initialValues = {
    name: monitor?.name ?? "",
    execution_start_date: CURRENT_DATE_ISO,
    execution_frequency: monitor?.execution_frequency,
  };

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
            {!isEditing && (
              <CustomDatePicker
                name="execution_start_date"
                label="Execution start date"
                id="execution_start_date"
                isRequired
                minValue={CURRENT_DATE_ISO}
              />
            )}
            <CustomSelect
              name="execution_frequency"
              id="execution_frequency"
              isRequired
              options={enumToOptions(MonitorFrequency)}
              label="Execution frequency"
              variant="stacked"
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
