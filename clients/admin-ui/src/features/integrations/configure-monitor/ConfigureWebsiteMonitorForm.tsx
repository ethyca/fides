import { format, parseISO } from "date-fns";
import { AntButton as Button, AntFlex as Flex, Icons, Text } from "fidesui";
import { Form, Formik } from "formik";
import { useRouter } from "next/router";
import * as Yup from "yup";

import { ControlledSelect } from "~/features/common/form/ControlledSelect";
import {
  CustomDateTimeInput,
  CustomTextInput,
} from "~/features/common/form/inputs";
import { enumToOptions } from "~/features/common/helpers";
import FormInfoBox from "~/features/common/modals/FormInfoBox";
import { MONITOR_CONFIG_ROUTE } from "~/features/common/nav/routes";
import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import { useGetOnlyCountryLocationsQuery } from "~/features/locations/locations.slice";
import { useGetSharedMonitorConfigsQuery } from "~/features/monitors/shared-monitor-config.slice";
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
  const router = useRouter();
  const integrationId = Array.isArray(router.query.id)
    ? router.query.id[0]
    : (router.query.id as string);
  const initialDate = monitor?.execution_start_date
    ? parseISO(monitor.execution_start_date)
    : Date.now();

  const { data: locationRegulationResponse, isLoading: locationsLoading } =
    useGetOnlyCountryLocationsQuery();

  const allSelectedRegions = [
    ...getSelectedRegionIds(locationRegulationResponse?.locations ?? []),
    ...getSelectedRegionIds(locationRegulationResponse?.location_groups ?? []),
  ];

  const { data: sharedMonitorConfigs } = useGetSharedMonitorConfigsQuery({
    page: 1,
    size: 100,
  });

  const sharedMonitorConfigOptions = sharedMonitorConfigs?.items.map(
    (config) => ({
      label: config.name,
      value: config.id,
    }),
  );

  const regionOptions = allSelectedRegions.map((region) => ({
    value: region,
    label: PRIVACY_NOTICE_REGION_RECORD[region],
  }));

  const initialValues: WebsiteMonitorConfig = {
    name: monitor?.name || "",
    execution_frequency:
      monitor?.execution_frequency || MonitorFrequency.NOT_SCHEDULED,
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
      key: monitor?.key,
      classify_params: monitor?.classify_params || {},
      datasource_params: values.datasource_params || {},
      connection_config_key: integrationId,
    };
    onSubmit(payload);
  };

  // Website monitors should only support
  // monthly, quarterly, yearly, and not scheduled frequencies
  const frequencyOptions = enumToOptions(MonitorFrequency).filter((option) =>
    [
      MonitorFrequency.MONTHLY,
      MonitorFrequency.QUARTERLY,
      MonitorFrequency.YEARLY,
      MonitorFrequency.NOT_SCHEDULED,
    ].includes(option.value as MonitorFrequency),
  );

  const handleViewSharedMonitorConfigs = () => {
    const a = document.createElement("a");
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.href = `${MONITOR_CONFIG_ROUTE}`;
    a.click();
    a.remove();
  };

  return (
    <Flex vertical className="pt-4">
      <FormInfoBox>
        <Text fontSize="sm">{FORM_COPY}</Text>
      </FormInfoBox>
      <Formik
        initialValues={initialValues}
        enableReinitialize
        onSubmit={handleSubmit}
        validationSchema={validationSchema}
      >
        {({ values, resetForm }) => (
          <Form>
            <Flex vertical gap="middle">
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
              <Flex className="w-full items-end gap-2">
                <ControlledSelect
                  name="shared_config_id"
                  id="shared_config_id"
                  options={sharedMonitorConfigOptions}
                  label="Shared monitor config"
                  tooltip="If a shared monitor config is selected, the monitor will use the shared config to classify resources"
                  layout="stacked"
                />
                <Button
                  onClick={handleViewSharedMonitorConfigs}
                  icon={<Icons.Settings />}
                  aria-label="View shared monitor configs"
                />
              </Flex>
              <ControlledSelect
                name="execution_frequency"
                id="execution_frequency"
                options={frequencyOptions}
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
              <Flex className="mt-2 justify-between">
                <Button
                  onClick={() => {
                    resetForm();
                    onClose();
                  }}
                >
                  Cancel
                </Button>
                <Button type="primary" htmlType="submit" data-testid="save-btn">
                  Save
                </Button>
              </Flex>
            </Flex>
          </Form>
        )}
      </Formik>
    </Flex>
  );
};

export default ConfigureWebsiteMonitorForm;
