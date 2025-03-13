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
import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import { formatKey } from "~/features/datastore-connections/add-connection/helpers";
import { useGetOnlyCountryLocationsQuery } from "~/features/locations/locations.slice";
import { getSelectedRegionIds } from "~/features/privacy-experience/form/helpers";
import {
  MonitorConfig,
  MonitorFrequency,
  WebsiteMonitorParams,
} from "~/types/api";

interface WebsiteMonitorConfig
  extends Omit<MonitorConfig, "datasource_params"> {
  datasource_params?: WebsiteMonitorParams;
  url: string;
}

const FORM_COPY = `This monitor allows you to simulate and verify user consent actions, such as 'accept,' 'reject,' or 'opt-out,' on consent experiences. For each detected activity, the monitor will record whether it occurred before or after the configured user actions, ensuring compliance with user consent choices.`;

const REGIONS_TOOLTIP_COPY = `Specify the region(s) to include in the scan. The monitor will scan the same URL across these locations to identify tracking technologies, such as cookies served by ad tech vendors.`;

const START_TIME_TOOLTIP_COPY = `Set the start time for the scan. For optimal performance and minimal disruption, schedule scans during periods of low traffic.`;

const validationSchema = Yup.object().shape({
  name: Yup.string().required().label("Name"),
  execution_frequency: Yup.string().nullable().label("Execution frequency"),
  execution_start_date: Yup.date().nullable().label("Execution start date"),
  datasource_params: Yup.object().shape({
    locations: Yup.array().label("Locations"),
    exclude_domains: Yup.array().label("Exclude domains"),
    sitemap_url: Yup.string().nullable().url().label("Sitemap URL"),
  }),
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

  const { data: locationRegulationResponse, isLoading: locationsLoading } =
    useGetOnlyCountryLocationsQuery();

  const allSelectedRegions = [
    ...getSelectedRegionIds(locationRegulationResponse?.locations ?? []),
    ...getSelectedRegionIds(locationRegulationResponse?.location_groups ?? []),
  ];

  const regionOptions = allSelectedRegions.map((region) => ({
    value: region,
    label: PRIVACY_NOTICE_REGION_RECORD[region],
  }));

  const initialValues: WebsiteMonitorConfig = {
    name: monitor?.name || "",
    execution_frequency:
      monitor?.execution_frequency || MonitorFrequency.MONTHLY,
    execution_start_date: format(initialDate, "yyyy-MM-dd'T'HH:mm"),
    url,
    connection_config_key: integrationId,
    datasource_params: (monitor?.datasource_params as WebsiteMonitorParams) ?? {
      locations: [],
    },
  };

  const handleSubmit = async (values: WebsiteMonitorConfig) => {
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

    const payload: WebsiteMonitorConfig = {
      ...monitor,
      ...values,
      ...executionInfo,
      key: monitor?.key || formatKey(values.name),
      classify_params: monitor?.classify_params || {},
      datasource_params: values.datasource_params || {},
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
        <Text fontSize="sm">{FORM_COPY}</Text>
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
                name="datasource_params.sitemap_url"
                id="sitemap_url"
                label="Sitemap URL"
                variant="stacked"
              />
              <ControlledSelect
                mode="tags"
                name="datasource_params.exclude_domains"
                placeholder="Enter domains to exclude"
                id="exclude_domains"
                label="Exclude domains"
                options={[]}
                open={false}
                layout="stacked"
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
                mode="multiple"
                isRequired
                name="datasource_params.locations"
                id="locations"
                label="Locations"
                loading={locationsLoading}
                options={regionOptions}
                optionFilterProp="label"
                tooltip={REGIONS_TOOLTIP_COPY}
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
                tooltip={START_TIME_TOOLTIP_COPY}
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
                <AntButton
                  type="primary"
                  htmlType="submit"
                  data-testid="save-btn"
                >
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
