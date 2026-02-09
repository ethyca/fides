import { ChakraFlex as Flex, Tag } from "fidesui";

const FieldDataTypeCell = ({ type }: { type?: string | null }) => (
  <Flex align="center" h="full">
    {!!type && <Tag>{type}</Tag>}
  </Flex>
);

export default FieldDataTypeCell;
