import { Badge, Flex } from "fidesui";

const FieldDataTypeCell = ({ type }: { type?: string | null }) => (
  <Flex align="center" h="full">
    {!!type && (
      <Badge fontSize="xs" fontWeight="normal">
        {type}
      </Badge>
    )}
  </Flex>
);

export default FieldDataTypeCell;
