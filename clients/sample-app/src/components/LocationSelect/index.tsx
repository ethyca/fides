import Image from "next/image";
import { useRouter } from "next/router";
import Select, { SingleValue } from "react-select";
import css from "./style.module.scss";

interface LocationOption {
  value: string;
  label: string;
  flag: string;
}

// Define the location options that the user can select from
// NOTE: this uses the https://hatscripts.github.io/circle-flags/ repo of prebuilt
// SVG flag icons, which has most countries but lacks specific flags for most
// region (ie. states/provinces/etc.). Therefore, be careful to only chose "flag" values
// that return a valid result for https://hatscripts.github.io/circle-flags/flags/${flag}.svg
const locationOptions: LocationOption[] = [
  { value: "US-CA", label: "California", flag: "us-ca" },
  { value: "US-VA", label: "Virginia", flag: "us" },
  { value: "US-NY", label: "New York", flag: "us" },
  { value: "FR-IDG", label: "Paris", flag: "fr" },
  { value: "DE-HE", label: "Frankfurt", flag: "de" },
];

// By default, each "option" in a <select> menu are plaintext labels, which is a
// bit dry, so this renders each option as a combo of a flag icon and the label
const formatOptionLabel = ({ label, flag }: LocationOption) => (
  <div className={css.option}>
    <Image
      alt=""
      src={`https://hatscripts.github.io/circle-flags/flags/${flag}.svg`}
      height="16"
      width="16"
    />
    <div>{label}</div>
  </div>
);

interface LocationSelectProps {
  menuPlacement: "bottom" | "auto" | "top"
}

const LocationSelect = ({ menuPlacement }: LocationSelectProps) => {
  // Inspect the query params of the current URL and set the default value of
  // the select input if a matching option is found.
  // e.g. http://localhost:3000/?location=US-CA -> select "California"
  const router = useRouter();
  const { location } = router.query;
  const defaultValue = locationOptions.find(
    (option) => option.value === location
  );

  // Whenever the user selects location option, reload the page and change the URL query param to suit
  // e.g. select "New York" -> navigate to http://localhost:3000?location=US-NY
  const onLocationSelect = (option: SingleValue<LocationOption>) => {
    if (!option) {
      router.query = {};
      router.push({ pathname: router.pathname, query: {} });
    } else {
      const { value } = option;
      router.push({ pathname: router.pathname, query: { location: value } });
    }
  };

  return (
    <div className={css.select}>
      <Select
        defaultValue={defaultValue}
        instanceId="location-select"
        isClearable
        formatOptionLabel={formatOptionLabel}
        menuPlacement={menuPlacement}
        options={locationOptions}
        onChange={onLocationSelect}
        placeholder="Select location..."
        styles={{
          container: (baseStyles) => ({
            ...baseStyles,
            width: "100%",
          }),
          control: (baseStyles) => ({
            ...baseStyles,
            background: "none",
          }),
        }}
      />
    </div>
  );
};

export default LocationSelect;
