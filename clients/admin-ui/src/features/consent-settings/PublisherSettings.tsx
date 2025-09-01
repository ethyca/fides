import {
  AntForm as Form,
  AntTypography as Typography,
  isoCodesToOptions,
  LocationSelect,
} from "fidesui";
import { useFormikContext } from "formik";

import { useFeatures } from "~/features/common/features";
import { useGetOnlyCountryLocationsQuery } from "~/features/locations/locations.slice";
import { getSelectedRegions } from "~/features/privacy-experience/form/helpers";

import SettingsBox from "./SettingsBox";

export type TCFPublisherSettings = {
  publisher_country_code?: string | null;
};

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
    <SettingsBox title="Publisher settings">
      <Typography.Paragraph className="mb-3">
        Specify the country in which your organization operates for TCF
        compliance. This setting will determine the &apos;Publisher Country Code
        &apos; transmitted in the Transparency and Consent (TC) Data.
      </Typography.Paragraph>
      <Form.Item label="Publisher country" htmlFor="publisher_country_code">
        <LocationSelect
          data-testid="input-publisher_settings.publisher_country_code"
          id="publisher_country_code"
          loading={locationsLoading}
          allowClear
          options={isoCodesToOptions(
            allSelectedCountries?.map((location) => location.id),
          )}
          placeholder="Select a country"
          value={values.tcfPublisherSettings.publisher_country_code
            ?.replace("_", "-")
            .toUpperCase()}
          onChange={(value) =>
            setFieldValue(
              "tcfPublisherSettings.publisher_country_code",
              value?.toLowerCase(),
            )
          }
          className="!w-80"
        />
      </Form.Item>
    </SettingsBox>
  ) : null;
};

export default PublisherSettings;
