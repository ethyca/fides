import { AntSelect as Select, AntTypography as Typography } from "fidesui";
import { useFormikContext } from "formik";

import { useFeatures } from "~/features/common/features";
import { useGetOnlyCountryLocationsQuery } from "~/features/locations/locations.slice";
import { getSelectedRegions } from "~/features/privacy-experience/form/helpers";
import { TCFPublisherSettings } from "~/types/api";

import SettingsBox from "./SettingsBox";

const PublisherSettings = () => {
  const { tcf: isTcfEnabled } = useFeatures();
  const { values, setFieldValue } = useFormikContext<{
    tcfPublisherSettings: TCFPublisherSettings;
  }>();
  const { data: locationRegulationResponse, isLoading: locationsLoading } =
    useGetOnlyCountryLocationsQuery();

  const allSelectedCountries = [
    ...getSelectedRegions(locationRegulationResponse?.locations ?? []),
    ...getSelectedRegions(locationRegulationResponse?.location_groups ?? []),
  ].sort((a, b) => (a.name < b.name ? -1 : 1));

  return isTcfEnabled ? (
    <SettingsBox title="Publisher Settings">
      <Typography.Paragraph className="mb-3">
        Specify the country in which your organization operates for TCF
        compliance. This setting will determine the &apos;Publisher Country Code
        &apos; transmitted in the Transparency and Consent (TC) Data.
      </Typography.Paragraph>
      {/* eslint-disable-next-line jsx-a11y/label-has-associated-control */}
      <label htmlFor="publisher_country_code" className="mb-1 block">
        <Typography.Text className="font-semibold">
          Publisher country
        </Typography.Text>
      </label>
      <Select
        data-testid="input-publisher_settings.publisher_country_code"
        id="publisher_country_code"
        loading={locationsLoading}
        allowClear
        options={allSelectedCountries?.map((location) => ({
          value: location.id,
          label: location.name,
        }))}
        showSearch
        optionFilterProp="label"
        placeholder="Select a country"
        value={values.tcfPublisherSettings.publisher_country_code}
        onChange={(value) =>
          setFieldValue("tcfPublisherSettings.publisher_country_code", value)
        }
        className="w-80"
      />
    </SettingsBox>
  ) : null;
};

export default PublisherSettings;
