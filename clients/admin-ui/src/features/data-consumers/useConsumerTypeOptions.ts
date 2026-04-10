import { useCallback, useMemo } from "react";

import {
  ConsumerTypeDefinition,
  useGetConsumerTypesQuery,
} from "./data-consumer.slice";

interface GroupedOption {
  label: string;
  options: { value: string; label: string }[];
}

const useConsumerTypeOptions = () => {
  const { data: consumerTypes, isLoading } = useGetConsumerTypesQuery();

  const typeOptions: GroupedOption[] = useMemo(() => {
    if (!consumerTypes?.length) {
      return [];
    }

    const groups = new Map<string, { value: string; label: string }[]>();
    consumerTypes.forEach((ct) => {
      const platformLabel = ct.platform_label;
      if (!groups.has(platformLabel)) {
        groups.set(platformLabel, []);
      }
      groups.get(platformLabel)!.push({ value: ct.key, label: ct.name });
    });

    return Array.from(groups.entries()).map(([label, options]) => ({
      label,
      options,
    }));
  }, [consumerTypes]);

  const getConsumerType = useCallback(
    (key: string): ConsumerTypeDefinition | undefined =>
      consumerTypes?.find((ct) => ct.key === key),
    [consumerTypes],
  );

  return { typeOptions, getConsumerType, isLoading };
};

export default useConsumerTypeOptions;
