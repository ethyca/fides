import { format, parseISO } from "date-fns";
import dayjs from "dayjs";
import {
  AntButton as Button,
  AntFlex as Flex,
  AntForm as Form,
  isoCodesToOptions,
  Text,
} from "fidesui";
import { getIn, useFormik } from "formik";
import { useRouter } from "next/router";
import * as Yup from "yup";

import { FormikDateTimeInput } from "~/features/common/form/FormikDateTimeInput";
import { FormikLocationSelect } from "~/features/common/form/FormikLocationSelect";
import { FormikSelect } from "~/features/common/form/FormikSelect";
import { FormikTextInput } from "~/features/common/form/FormikTextInput";
import { enumToOptions } from "~/features/common/helpers";
import FormInfoBox from "~/features/common/modals/FormInfoBox";
import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import { useGetOnlyCountryLocationsQuery } from "~/features/locations/locations.slice";
import { getSelectedRegionIds } from "~/features/privacy-experience/form/helpers";
import {
  MonitorConfig,
  MonitorFrequency,
  WebsiteMonitorParams,
} from "~/types/api";

import { FormikSharedConfigSelect } from "./FormikSharedConfigSelect";

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

  const regionOptions = allSelectedRegions.map((region) => ({
    value: region,
    label: PRIVACY_NOTICE_REGION_RECORD[region],
  }));

  const initialValues: WebsiteMonitorConfig = {
    name: monitor?.name || "",
    shared_config_id: monitor?.shared_config_id ?? undefined,
    execution_frequency:
      monitor?.execution_frequency || MonitorFrequency.NOT_SCHEDULED,
    execution_start_date: format(initialDate, "yyyy-MM-dd'T'HH:mm"),
    url,
    connection_config_key: integrationId,
    datasource_params: (monitor?.datasource_params as WebsiteMonitorParams) ?? {
      locations: [],
      exclude_domains: [],
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

  const {
    values,
    resetForm,
    handleSubmit: formikSubmit,
    errors,
    touched,
    ...formik
  } = useFormik({
    initialValues,
    onSubmit: handleSubmit,
    validationSchema,
  });

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

  return (
    <Flex vertical className="pt-4">
      <FormInfoBox>
        <Text fontSize="sm">{FORM_COPY}</Text>
      </FormInfoBox>
      <Form onFinish={formikSubmit} layout="vertical">
        <FormikTextInput
          name="name"
          id="name"
          label="Name"
          required
          error={errors.name}
          touched={touched.name}
          onChange={formik.handleChange}
          onBlur={formik.handleBlur}
          value={values.name}
        />
        <FormikTextInput
          name="datasource_params.sitemap_url"
          id="sitemap_url"
          label="Sitemap URL"
          error={getIn(errors, "datasource_params.sitemap_url")}
          touched={getIn(touched, "datasource_params.sitemap_url")}
          onChange={formik.handleChange}
          onBlur={formik.handleBlur}
          value={values.datasource_params?.sitemap_url || ""}
        />
        <FormikSelect
          name="datasource_params.exclude_domains"
          placeholder="Enter domains to exclude"
          id="exclude_domains"
          label="Exclude domains"
          mode="tags"
          options={[]}
          suffixIcon={null}
          open={false}
          error={getIn(errors, "datasource_params.exclude_domains")}
          touched={getIn(touched, "datasource_params.exclude_domains")}
          onChange={(value) =>
            formik.setFieldValue("datasource_params.exclude_domains", value)
          }
          onBlur={formik.handleBlur}
          value={values.datasource_params?.exclude_domains || []}
        />
        <FormikTextInput
          name="url"
          id="url"
          label="URL"
          required
          disabled
          error={errors.url}
          touched={touched.url}
          onChange={formik.handleChange}
          onBlur={formik.handleBlur}
          value={values.url || ""}
        />
        <FormikLocationSelect
          id="locations"
          name="datasource_params.locations"
          label="Locations"
          loading={locationsLoading}
          options={isoCodesToOptions(
            regionOptions.map((option) => option.value),
          )}
          required
          tooltip={REGIONS_TOOLTIP_COPY}
          mode="multiple"
          error={getIn(errors, "datasource_params.locations")}
          touched={getIn(touched, "datasource_params.locations")}
          onChange={(value) =>
            formik.setFieldValue("datasource_params.locations", value)
          }
          onBlur={formik.handleBlur}
          value={values.datasource_params?.locations}
        />
        <FormikSharedConfigSelect
          name="shared_config_id"
          id="shared_config_id"
          error={errors.shared_config_id}
          touched={touched.shared_config_id}
          onChange={(value) => formik.setFieldValue("shared_config_id", value)}
          onBlur={formik.handleBlur}
          value={values.shared_config_id}
        />
        <FormikSelect
          name="execution_frequency"
          id="execution_frequency"
          options={frequencyOptions}
          label="Automatic execution frequency"
          error={errors.execution_frequency}
          touched={touched.execution_frequency}
          onChange={(value) =>
            formik.setFieldValue("execution_frequency", value)
          }
          onBlur={formik.handleBlur}
          value={values.execution_frequency}
        />
        <FormikDateTimeInput
          name="execution_start_date"
          label="Automatic execution start time"
          disabled={
            values.execution_frequency === MonitorFrequency.NOT_SCHEDULED
          }
          id="execution_start_date"
          tooltip={START_TIME_TOOLTIP_COPY}
          error={errors.execution_start_date}
          touched={touched.execution_start_date}
          onChange={(value) =>
            value &&
            formik.setFieldValue("execution_start_date", value.toISOString())
          }
          onBlur={formik.handleBlur}
          value={dayjs(values.execution_start_date)}
        />
        <Flex className="mt-2" justify="stretch">
          <Button
            onClick={() => {
              resetForm();
              onClose();
            }}
            block
          >
            Cancel
          </Button>
          <Button type="primary" htmlType="submit" data-testid="save-btn" block>
            Save
          </Button>
        </Flex>
      </Form>
    </Flex>
  );
};

export default ConfigureWebsiteMonitorForm;
