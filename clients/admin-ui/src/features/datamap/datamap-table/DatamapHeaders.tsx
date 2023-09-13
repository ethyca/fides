import { HeaderGroup } from "react-table";

import GroupedHeader from "~/features/common/table/grouped/GroupedHeader";
import type { DatamapRow } from "~/features/datamap/datamap.slice";

interface DatamapHeadersProps {
  headerGroups: HeaderGroup<DatamapRow>[];
}

const DatamapHeaders: React.FC<DatamapHeadersProps> = ({ headerGroups }) => (
  <GroupedHeader<DatamapRow> headerGroups={headerGroups} />
);

export default DatamapHeaders;
