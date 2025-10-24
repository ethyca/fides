import { DefaultOptionType } from "antd/es/select";
import { AntSelect as Select } from "fidesui";
import type { ISO31661Entry, ISO31662Entry } from "iso-3166";
import { iso31661, iso31662 } from "iso-3166";
import { useMemo } from "react";

import {
  ICustomMultiSelectProps,
  ICustomSelectProps,
} from "../../hoc/CustomSelect";
import {
  formatIsoLocation,
  isoCodeToFlag,
} from "../data-display/location.utils";

export const isoCodesToOptions = (isoCodes: string[]) =>
  isoCodes.reduce(
    (agg, current) => {
      const region = iso31662.find(
        (entry) => entry.code === current.toUpperCase(),
      );
      const country = iso31661.find(
        (entry) => entry.alpha2 === current.toUpperCase(),
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
  value?: string | null;
  label?: string | null;
  title?: string;
  country: string;
  subdivision?: string;
  flag: string;
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

interface ILocationSelectProps
  extends Omit<ICustomSelectProps<string>, "options"> {}
interface ILocationMultiSelectProps
  extends Omit<ICustomMultiSelectProps<string>, "options"> {}

export type LocationSelectProps = (
  | ILocationSelectProps
  | ILocationMultiSelectProps
) & {
  options?: LocationOptions;
};

export const LocationSelect = (props: LocationSelectProps) => {
  const {
    mode,
    options: { countries, regions } = {
      countries: iso31661,
      regions: iso31662,
    },
  } = props;

  const defaultProps = {
    "data-testid": "iso_select",
    id: "iso_select",
    allowClear: true,
    showSearch: true,
    optionFilterProp: "label",
    filterSort: (left: IsoOption, right: IsoOption) =>
      (left?.label ?? "")
        .toLowerCase()
        .localeCompare((right?.label ?? "").toLowerCase()),

    filterOption: (input: string, option?: IsoOption) =>
      option?.value?.toLowerCase().includes(input.toLowerCase()) ||
      option?.label?.toLowerCase().includes(input.toLowerCase()) ||
      false,
  };

  const userTranslation = new Intl.DisplayNames(navigator.language, {
    type: "region",
  });

  const isoSelectOptions = useMemo(
    () =>
      mapIsoObjects(countries, regions).map(([country, subdivision]) => ({
        value: subdivision?.code ?? country.alpha2,
        label: formatIsoLocation({
          userTranslation,
          isoEntry: subdivision ?? country,
          showFlag: true,
        }),
        title: formatIsoLocation({
          userTranslation,
          isoEntry: subdivision ?? country,
          showFlag: false,
        }),
        country: formatIsoLocation({ userTranslation, isoEntry: country }),
        subdivision: subdivision?.name,
        flag: isoCodeToFlag(country.alpha2),
      })),
    [countries, regions, navigator.language],
  );

  return (
    <Select<string, IsoOption>
      placeholder={mode ? "🌐 Select locations" : "🌐 Select location"}
      {...defaultProps}
      {...props}
      options={isoSelectOptions}
      /**
       * @description this must be set to true to prevent performance issues
       */
      popupMatchSelectWidth
    />
  );
};
