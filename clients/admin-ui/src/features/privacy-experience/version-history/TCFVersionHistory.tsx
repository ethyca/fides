// PROTOTYPE — delete with TCF history
import { Alert, Flex } from "fidesui";
import { useMemo, useState } from "react";

import { PRIVACY_EXPERIENCE_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";

import {
  getSourceFilterValue,
  MOCK_TCF_EXPERIENCE_ID,
  MOCK_TCF_EXPERIENCE_NAME,
  MOCK_TCF_HISTORY,
} from "./mockHistory";
import {
  VersionHistoryFilters,
  VersionHistoryFiltersState,
} from "./VersionHistoryFilters";
import { VersionHistoryList } from "./VersionHistoryList";

const INITIAL_FILTERS: VersionHistoryFiltersState = {
  search: "",
  types: [],
  users: [],
  from: null,
  to: null,
};

export const TCFVersionHistory = ({
  experienceId = MOCK_TCF_EXPERIENCE_ID,
  experienceName = MOCK_TCF_EXPERIENCE_NAME,
}: {
  experienceId?: string;
  experienceName?: string;
}) => {
  const [filters, setFiltersState] =
    useState<VersionHistoryFiltersState>(INITIAL_FILTERS);

  const setFilters = (next: Partial<VersionHistoryFiltersState>) =>
    setFiltersState((prev) => ({ ...prev, ...next }));

  const filteredEvents = useMemo(() => {
    const search = filters.search.trim().toLowerCase();
    const fromTime = filters.from
      ? new Date(`${filters.from}T00:00:00`).getTime()
      : null;
    const toTime = filters.to
      ? new Date(`${filters.to}T23:59:59.999`).getTime()
      : null;
    return MOCK_TCF_HISTORY.filter((event) => {
      if (filters.types.length > 0 && !filters.types.includes(event.type)) {
        return false;
      }
      if (
        filters.users.length > 0 &&
        !filters.users.includes(getSourceFilterValue(event.source))
      ) {
        return false;
      }
      if (fromTime !== null || toTime !== null) {
        const eventTime = new Date(event.timestamp).getTime();
        if (fromTime !== null && eventTime < fromTime) {
          return false;
        }
        if (toTime !== null && eventTime > toTime) {
          return false;
        }
      }
      if (search.length > 0) {
        const hashMatch =
          (event.previousHash?.toLowerCase().includes(search) ?? false) ||
          event.newHash.toLowerCase().includes(search);
        if (!hashMatch) {
          return false;
        }
      }
      return true;
    });
  }, [filters]);

  return (
    <Flex vertical gap="middle" className="w-full">
      <PageHeader
        heading={`${experienceName} version history`}
        breadcrumbItems={[
          {
            title: "Privacy experiences",
            href: PRIVACY_EXPERIENCE_ROUTE,
          },
          {
            title: experienceName,
            href: `${PRIVACY_EXPERIENCE_ROUTE}/${experienceId}`,
          },
          { title: `${experienceName} version history` },
        ]}
        isSticky={false}
      />
      <Alert
        type="info"
        showIcon
        message="About version history"
        description={`Version history shows every change made to this ${experienceName} experience — including updates from Fides automation (e.g. Compass sync) and edits by your team. Each entry shows the configuration hash before and after the change.`}
      />
      <VersionHistoryFilters filters={filters} setFilters={setFilters} />
      <VersionHistoryList events={filteredEvents} />
    </Flex>
  );
};
