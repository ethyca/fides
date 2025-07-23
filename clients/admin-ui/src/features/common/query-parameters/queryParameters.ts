/* eslint-disable react/no-unstable-nested-components */
import dayjs, { Dayjs } from "dayjs";
import { useSearchParams } from "next/navigation";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

const toDayjs = (v: string): dayjs.Dayjs => dayjs(v);
const toIsoString = (v: dayjs.Dayjs | null): string => v?.toISOString() ?? "";
export const safeParseInt = (value: string) => {
  const parsed = parseInt(value, 10);
  if (!Number.isNaN(parsed) && Number.isFinite(parsed)) {
    return parsed;
  }
  return 1;
};

export function useStatefulQueryParam<InitialValue = string>(
  key: string,
  fromQueryParam: (value: string) => InitialValue,
  initialValue: InitialValue,
  toQueryParam: (value: InitialValue) => string = (value) =>
    value?.toString() ?? "",
) {
  const searchParams = useSearchParams();
  const paramValue = searchParams?.get(key) ?? null;
  const initialState =
    (paramValue ? fromQueryParam(paramValue) : null) ?? initialValue;
  const [value, setValue] = useState(initialState);
  const router = useRouter();

  useEffect(() => {
    const nextQueryParams = new URLSearchParams(searchParams ?? {});
    if (value === initialValue || value === undefined || value === null) {
      nextQueryParams.delete(key);
    } else {
      nextQueryParams.set(
        key,
        toQueryParam ? toQueryParam(value).toString() : value.toString(),
      );
    }
    const nextQueryParamString = nextQueryParams.toString();
    if (nextQueryParamString !== searchParams?.toString()) {
      router.push({
        query: nextQueryParamString,
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, paramValue, value, searchParams]);

  return [value, setValue] as const;
}

export const useDateQueryParam = (key: string) => {
  return useStatefulQueryParam<Dayjs | null>(key, toDayjs, null, toIsoString);
};
