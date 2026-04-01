import { Select, SelectProps } from "fidesui";
import { useMemo } from "react";

import { useGetAllPrivacyNoticesQuery } from "~/features/privacy-notices/privacy-notices.slice";

type PrivacyNoticeSelectProps = Omit<SelectProps, "options">;

/**
 * Select that fetches privacy notices, displays them by name in the dropdown,
 * but shows the notice_key as the selected value.
 */
const PrivacyNoticeSelect = (props: PrivacyNoticeSelectProps) => {
  const { data, isFetching } = useGetAllPrivacyNoticesQuery({
    page: 1,
    size: 100,
  });

  const options = useMemo(
    () =>
      data?.items?.map((notice) => ({
        value: notice.notice_key,
        label: `${notice.name} (${notice.notice_key})`,
      })) ?? [],
    [data],
  );

  return (
    <Select
      showSearch
      placeholder="Search privacy notices..."
      aria-label="Select privacy notice"
      options={options}
      loading={isFetching}
      data-testid="privacy-notice-select"
      {...props}
    />
  );
};

export default PrivacyNoticeSelect;
