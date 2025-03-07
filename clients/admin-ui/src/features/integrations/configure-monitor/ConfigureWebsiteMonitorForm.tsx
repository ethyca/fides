import { format, parseISO } from "date-fns";
import { AntButton, AntFlex, Box, Text } from "fidesui";
import { Form, Formik } from "formik";
import { useRouter } from "next/router";
import * as Yup from "yup";

import { ControlledSelect } from "~/features/common/form/ControlledSelect";
import {
  CustomDateTimeInput,
  CustomTextInput,
} from "~/features/common/form/inputs";
import { enumToOptions } from "~/features/common/helpers";
import { PRIVACY_NOTICE_REGION_OPTIONS } from "~/features/common/privacy-notice-regions";
import { MonitorConfig, MonitorFrequency } from "~/types/api";

const COPY = `This monitor allows you to simulate and verify user consent actions, such as 'accept,' 'reject,' or 'opt-out,' on consent experiences. For each detected activity, the monitor will record whether it occurred before or after the configured user actions, ensuring compliance with user consent choices.`;

const validationSchema = Yup.object().shape({
  name: Yup.string().required().label("Name"),
  execution_frequency: Yup.string().nullable().label("Execution frequency"),
  execution_start_date: Yup.date().nullable().label("Execution start date"),
});

const ConfigureWebsiteMonitorForm = ({
  monitor,
  url,
  onClose,
  onSubmit,
}: {
  monitor?: MonitorConfig;
  url: string;
  onClose: () => void;
  onSubmit: (values: MonitorConfig) => Promise<void>;
}) => {
  const { query } = useRouter();
  const integrationId = Array.isArray(query.id)
    ? query.id[0]
    : (query.id as string);
  const initialDate = monitor?.execution_start_date
    ? parseISO(monitor.execution_start_date)
    : Date.now();

  const initialValues = {
    name: monitor?.name || "",
    execution_frequency:
      monitor?.execution_frequency || MonitorFrequency.MONTHLY,
    execution_start_date: format(initialDate, "yyyy-MM-dd'T'HH:mm"),
    url,
    connection_config_key: integrationId,
  };

  const handleSubmit = async (values: MonitorConfig) => {
    const executionInfo =
      values.execution_frequency !== MonitorFrequency.NOT_SCHEDULED
        ? {
            execution_frequency: values.execution_frequency,
            execution_start_date: new Date(
              values.execution_start_date!,
            ).toISOString(),
          }
        : {
            execution_frequency: MonitorFrequency.NOT_SCHEDULED,
            execution_start_date: undefined,
          };

    const payload: MonitorConfig = {
      ...monitor,
      ...executionInfo,
      name: values.name,
      connection_config_key: integrationId,
    };
    onSubmit(payload);
  };

  return (
    <AntFlex vertical className="pt-4">
      <Box
        p={4}
        mb={4}
        border="1px solid"
        borderColor="gray.200"
        bgColor="gray.50"
        borderRadius="md"
      >
        <Text fontSize="sm">{COPY}</Text>
      </Box>
      <Formik
        initialValues={initialValues}
        enableReinitialize
        onSubmit={handleSubmit}
        validationSchema={validationSchema}
      >
        {({ values, resetForm }) => (
          <Form>
            <AntFlex vertical gap="middle">
              <CustomTextInput
                name="name"
                id="name"
                label="Name"
                isRequired
                variant="stacked"
              />
              <CustomTextInput
                name="url"
                id="url"
                label="URL"
                isRequired
                disabled
                variant="stacked"
              />
              <ControlledSelect
                mode="tags"
                isRequired
                name="datasource_params.locations"
                id="locations"
                label="Locations"
                options={PRIVACY_NOTICE_REGION_OPTIONS}
                layout="stacked"
              />
              <ControlledSelect
                name="execution_frequency"
                id="execution_frequency"
                options={enumToOptions(MonitorFrequency)}
                label="Automatic execution frequency"
                layout="stacked"
              />
              <CustomDateTimeInput
                name="execution_start_date"
                label="Automatic execution start time"
                disabled={
                  values.execution_frequency === MonitorFrequency.NOT_SCHEDULED
                }
                id="execution_start_date"
              />
              <AntFlex className="mt-2 justify-between">
                <AntButton
                  onClick={() => {
                    resetForm();
                    onClose();
                  }}
                >
                  Cancel
                </AntButton>
                <AntButton type="primary" htmlType="submit">
                  Save
                </AntButton>
              </AntFlex>
            </AntFlex>
          </Form>
        )}
      </Formik>
    </AntFlex>
  );
};

export default ConfigureWebsiteMonitorForm;
