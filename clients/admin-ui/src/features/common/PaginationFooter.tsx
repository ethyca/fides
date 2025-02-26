import { AntButton as Button, Flex, Text } from "fidesui";

type PaginationFooterProps = {
  page: number;
  size: number;
  total: number;
  handleNextPage: () => void;
  handlePreviousPage: () => void;
};

const PaginationFooter = ({
  page,
  size,
  total,
  handleNextPage,
  handlePreviousPage,
}: PaginationFooterProps) => {
  const startingItem = (page - 1) * size + 1;
  const endingItem = Math.min(total, page * size);
  return (
    <Flex justifyContent="space-between" mt={6}>
      <Text fontSize="xs" color="gray.600">
        {total > 0 ? (
          <>
            Showing {Number.isNaN(startingItem) ? 0 : startingItem} to{" "}
            {Number.isNaN(endingItem) ? 0 : endingItem} of{" "}
            {Number.isNaN(total) ? 0 : total} results
          </>
        ) : (
          "0 results"
        )}
      </Text>
      <div>
        <Button
          disabled={page <= 1}
          onClick={handlePreviousPage}
          className="mr-2"
        >
          Previous
        </Button>
        <Button disabled={page * size >= total} onClick={handleNextPage}>
          Next
        </Button>
      </div>
    </Flex>
  );
};

export default PaginationFooter;
