import {
  AntForm as Form,
  AntSelect as Select,
  AntTypography as Typography,
} from "fidesui";
import { useFormikContext } from "formik";

import { useFeatures } from "~/features/common/features";
import { useGetOnlyCountryLocationsQuery } from "~/features/locations/locations.slice";
import { getSelectedRegions } from "~/features/privacy-experience/form/helpers";
import { TCFPublisherSettings } from "~/types/api";

import SettingsBox from "./SettingsBox";

const PublisherSettings = () => {
  const { tcf: isTcfEnabled } = useFeatures();
  const { initialValues, values, setFieldValue } = useFormikContext<{
    tcfPublisherSettings: TCFPublisherSettings;
  }>();
  const { data: locationRegulationResponse, isLoading: locationsLoading } =
    useGetOnlyCountryLocationsQuery();

  const allSelectedCountries = [
    ...getSelectedRegions(locationRegulationResponse?.locations ?? []),
    ...getSelectedRegions(locationRegulationResponse?.location_groups ?? []),
  ].sort((a, b) => (a.name < b.name ? -1 : 1));

  const allOptions = [
    // { id: NO_COUNTRY_SELECTED, name: "AA" },
    ...allSelectedCountries,
  ];

  return isTcfEnabled ? (
    <SettingsBox title="Publisher Settings">
      <Typography.Paragraph className="mb-3">
        Specify the country in which your organization operates for TCF
        compliance. This setting will determine the &apos;Publisher Country Code
        &apos; transmitted in the Transparency and Consent (TC) Data.
      </Typography.Paragraph>
      <Form.Item
        label="Publisher country"
        name={["publisher", "country_code"]}
        layout="vertical"
        className="w-80"
      >
        <Select
          id="publisher_country_code"
          loading={locationsLoading}
          allowClear
          options={allOptions?.map((location) => ({
            value: location.id,
            label: location.name,
          }))}
          defaultValue={
            initialValues.tcfPublisherSettings.publisher_country_code
          }
          showSearch
          optionFilterProp="label"
          placeholder="Select a country"
          value={values.tcfPublisherSettings.publisher_country_code}
          onChange={(value) =>
            setFieldValue("tcfPublisherSettings.publisher_country_code", value)
          }
        />
      </Form.Item>
    </SettingsBox>
  ) : null;
};

export default PublisherSettings;
