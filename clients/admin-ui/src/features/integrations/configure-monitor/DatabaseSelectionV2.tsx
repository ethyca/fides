import { Text } from "fidesui";
import FidesSpinner from "~/features/common/FidesSpinner";

import { useGetDatabasesByConnectionQuery } from "~/features/data-discovery-and-detection/discovery-detection.slice";

const DatabaseSelectionV2 = ({
  integrationKey,
}: {
  integrationKey: string;
}) => {
  //   const {
  //     PAGE_SIZES,
  //     pageSize,
  //     setPageSize,
  //     onPreviousPageClick,
  //     isPreviousPageDisabled,
  //     onNextPageClick,
  //     isNextPageDisabled,
  //     startRange,
  //     endRange,
  //     pageIndex,
  //     setTotalPages,
  //   } = useServerSidePagination();

  const { data, isLoading, isFetching } = useGetDatabasesByConnectionQuery({
    page: 1,
    size: 25,
    connection_config_key: integrationKey,
  });

  console.log(data);

  return isLoading ? <FidesSpinner /> : <Text>hello world!</Text>;
};

export default DatabaseSelectionV2;
