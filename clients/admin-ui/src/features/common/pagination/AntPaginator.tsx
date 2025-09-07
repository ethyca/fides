import { AntPagination as Paginator, PropsOf } from "fidesui";

import { useAntPaginationContext } from "./PaginationProvider";

const AntPaginator = (
  props: Omit<
    PropsOf<typeof Paginator>,
    keyof ReturnType<typeof useAntPaginationContext>
  >,
) => {
  const { paginationProps } = useAntPaginationContext();

  return (
    <Paginator
      {...paginationProps}
      {...props}
      showTotal={(total, range) => `${range[0]}-${range[1]} of ${total} items`}
    />
  );
};

export default AntPaginator;
