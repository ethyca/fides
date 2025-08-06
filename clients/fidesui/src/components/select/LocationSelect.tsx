import { DefaultOptionType } from "antd/es/select";
import { SelectProps } from "antd/lib";
import { AntSelect as Select, AntTag as Tag } from "fidesui";
import type { ISO31661Entry, ISO31662Entry } from "iso-3166";
import { iso31661, iso31662 } from "iso-3166";
import { ComponentProps, ReactNode, useMemo, useState } from "react";

import { isoEntryToFormattedText, IsoFlag } from "../data-display/Location";

export const isoCodesToOptions = (codes: string[]) =>
  codes.reduce(
    (agg, current) => {
      const region = iso31662.find(
        (entry) => entry.code.toLowerCase() === current.toLowerCase(),
      );
      const country = iso31661.find(
        (entry) => entry.alpha2.toLowerCase() === current.toLowerCase(),
      );

      if (region) {
        return {
          ...agg,
          regions: [...agg.regions, region],
        };
      }
      if (country) {
        return {
          ...agg,
          countries: [...agg.countries, country],
        };
      }
      return agg;
    },
    { countries: [], regions: [] } as LocationOptions,
  );

type LocationOptions = {
  countries: Array<ISO31661Entry>;
  regions: Array<ISO31662Entry>;
};

interface IsoOption extends DefaultOptionType {
  country: string;
  subdivision?: string;
  flag: ReactNode;
  value?: string | null;
  label?: string | null;
}

const mapIsoObjects = (
  countries: ISO31661Entry[],
  subdivisions: ISO31662Entry[],
): [ISO31661Entry, ISO31662Entry | null][] => {
  const mapped = countries.map((country) => {
    const children: [ISO31661Entry, ISO31662Entry][] = subdivisions
      .filter(({ parent }) => country.alpha2 === parent)
      .map((child) => [country, child]);

    return children.length > 0
      ? children
      : [[country, null] as [ISO31661Entry, null]];
  });

  return mapped.flat();
};

type LocationSelectProps = Omit<
  ComponentProps<typeof Select<string, IsoOption>>,
  "options"
> & {
  options?: LocationOptions;
};

const LocationSelectOption: SelectProps<string, IsoOption>["optionRender"] = (
  option,
) => {
  const {
    data: { subdivision, flag, country },
  } = option;
  return (
    <>
      {flag} {subdivision ? `${country} / ${subdivision}` : country}
    </>
  );
};

const LocationTag: SelectProps<string, IsoOption>["tagRender"] = (prop) => {
  const { label, value, onClose, closable } = prop;
  return (
    <Tag
      onClose={onClose}
      closable={closable}
      style={{
        fontSize: "var(--ant-font-size)",
        marginInlineEnd:
          "calc(var(--ant-select-internal_fixed_item_margin) * 2)",
      }}
    >
      <IsoFlag isoCode={value} /> {label}
    </Tag>
  );
};

export const LocationSelect = ({
  options = { countries: iso31661, regions: iso31662 },
  onChange,
  ...props
}: LocationSelectProps) => {
  const countries = options.countries ?? iso31661;
  const regions = options.regions ?? [];

  const [internalValue, setValue] = useState(props.value);

  const userTranslation = new Intl.DisplayNames(navigator.language, {
    type: "region",
  });

  const isoSelectOptions = useMemo(
    () =>
      mapIsoObjects(countries, regions).map(([country, subdivision]) => ({
        value: subdivision?.code ?? country.alpha2,
        label: isoEntryToFormattedText(userTranslation, subdivision ?? country),
        country: isoEntryToFormattedText(userTranslation, country),
        subdivision: subdivision?.name,
        flag: <IsoFlag isoCode={country.alpha2} />,
      })),
    [countries, regions, navigator.language],
  );

  return (
    <Select
      data-testid="iso_select"
      id="iso_select"
      allowClear
      options={isoSelectOptions}
      showSearch
      optionFilterProp="label"
      placeholder={!props.mode ? "Select location" : "🌐 Select locations"}
      prefix={!props.mode && <IsoFlag isoCode={internalValue} fallback="🌐" />}
      optionRender={LocationSelectOption}
      labelRender={(label) => label.label}
      tagRender={LocationTag}
      filterOption={(input, option) =>
        option?.value?.toLowerCase().includes(input.toLowerCase()) ||
        option?.label?.toLowerCase().includes(input.toLowerCase()) ||
        false
      }
      filterSort={(left, right) =>
        (left?.label ?? "")
          .toLowerCase()
          .localeCompare((right?.label ?? "").toLowerCase())
      }
      {...props}
      /**
       * @description this must be set to true to prevent performance issues
       */
      popupMatchSelectWidth
      onChange={(newValue, option) => {
        /** eslint made me do this */
        if (props.value) {
          setValue(newValue);
        }
        if (onChange) {
          onChange(newValue, option);
        }
      }}
    />
  );
};
