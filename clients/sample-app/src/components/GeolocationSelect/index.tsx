import Image from "next/image";
import { useRouter } from "next/router";
import Select, { SingleValue } from "react-select";

import css from "./style.module.scss";

interface GeolocationOption {
  value: string;
  label: string;
  flag: string;
}

// Define the geolocation options that the user can select from
// NOTE: this uses the https://hatscripts.github.io/circle-flags/ repo of prebuilt
// SVG flag icons, which has most countries but lacks specific flags for most
// region (ie. states/provinces/etc.). Therefore, be careful to only chose "flag" values
// that return a valid result for https://hatscripts.github.io/circle-flags/flags/${flag}.svg
const geolocationOptions: GeolocationOption[] = [
  { value: "US-CA", label: "California", flag: "us-ca" },
  { value: "US-VA", label: "Virginia", flag: "us" },
  { value: "US-NY", label: "New York", flag: "us" },
  { value: "CA", label: "Canada", flag: "ca" },
  { value: "CA-QC", label: "Quebec", flag: "ca-qc" },
  { value: "EEA", label: "EEA", flag: "eu" },
  { value: "FR-IDG", label: "Paris", flag: "fr" },
  { value: "DE-HE", label: "Frankfurt", flag: "de" },
];

// By default, each "option" in a <select> menu are plaintext labels, which is a
// bit dry, so this renders each option as a combo of a flag icon and the label
const formatOptionLabel = ({ label, flag }: GeolocationOption) => (
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

interface GeolocationSelectProps {
  menuPlacement: "bottom" | "auto" | "top";
}

const GeolocationSelect = ({ menuPlacement }: GeolocationSelectProps) => {
  // Inspect the query params of the current URL and set the default value of
  // the select input if a matching option is found.
  // e.g. http://localhost:3000/?geolocation=US-CA -> select "California"
  const router = useRouter();
  const { geolocation } = router.query;
  const defaultValue = geolocationOptions.find(
    (option) => option.value === geolocation,
  );

  // Whenever the user selects geolocation option, change the URL query param to suit
  // (e.g. select "New York" -> navigate to http://localhost:3000?geolocation=US-NY)
  // Then, after updating the URL, force a page reload to run the fides.js script again, etc.
  const onGeolocationSelect = (option: SingleValue<GeolocationOption>) => {
    if (!option) {
      router.query = {};
      router
        .push({ pathname: router.pathname, query: {} })
        .then(() => router.reload());
    } else {
      const { value } = option;
      router
        .push({ pathname: router.pathname, query: { geolocation: value } })
        .then(() => router.reload());
    }
  };

  return (
    <div className={css.select}>
      <Select
        defaultValue={defaultValue}
        instanceId="geolocation-select"
        isClearable
        formatOptionLabel={formatOptionLabel}
        menuPlacement={menuPlacement}
        options={geolocationOptions}
        onChange={onGeolocationSelect}
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

export default GeolocationSelect;
