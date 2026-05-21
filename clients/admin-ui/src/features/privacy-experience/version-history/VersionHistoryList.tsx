// PROTOTYPE — delete with TCF history
import { Empty, List } from "fidesui";

import { HistoryEvent } from "./mockHistory";
import { VersionHistoryListItem } from "./VersionHistoryListItem";

interface VersionHistoryListProps {
  events: HistoryEvent[];
}

export const VersionHistoryList = ({ events }: VersionHistoryListProps) => (
  <List<HistoryEvent>
    dataSource={events}
    locale={{
      emptyText: (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="No history events match these filters."
        />
      ),
    }}
    renderItem={(event) => <VersionHistoryListItem event={event} />}
  />
);
