import Image from "next/image";
import { useRouter } from "next/router";
import Select, { SingleValue } from "react-select";
import css from "./style.module.scss";

interface LocationOption {
  value: string;
  label: string;
  flag: string;
}

const locationOptions: LocationOption[] = [
  { value: "US-CA", label: "California", flag: "us-ca" },
  { value: "US-VA", label: "Virginia", flag: "us" },
  { value: "US-NY", label: "New York", flag: "us" },
  { value: "FR-IDG", label: "Paris", flag: "fr" },
  { value: "DE-HE", label: "Frankfurt", flag: "de" },
];

const formatOptionLabel = ({ label, flag }: LocationOption) => (
  <div className={css.option}>
    <Image alt="" src={`https://hatscripts.github.io/circle-flags/flags/${flag}.svg`} width="16" />
    <div>{label}</div>
  </div>
)

const Header = () => {
  const router = useRouter();
  const { location } = router.query;
  const defaultValue = locationOptions.find(option => option.value === location);

  const onLocationSelect = (option: SingleValue<LocationOption>) => {
    if (!option) {
      router.push("/");
    } else {
      const { value } = option;
      router.push(`/?location=${value}`);
    }
  }

  return (
    <header className={css.header}>
      <Image src="/logo.svg" width={204} height={68} alt="Logo" />
      <div className={css.select}>
        <Select
          defaultValue={defaultValue}
          instanceId="location-select"
          isClearable
          formatOptionLabel={formatOptionLabel}
          options={locationOptions}
          onChange={onLocationSelect}
          placeholder="Location..."
          styles={{
            container: (baseStyles) => ({
              ...baseStyles,
              width: "100%"
            }),
            control: (baseStyles) => ({
              ...baseStyles,
              background: "none"
            })
          }}
        />
      </div>
    </header>
  );
}

export default Header;
