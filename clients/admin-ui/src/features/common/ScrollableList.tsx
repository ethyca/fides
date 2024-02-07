import {
  Box,
  Divider,
  DragHandleIcon,
  Flex,
  List,
  StackDivider,
  Text,
  useToken,
} from "@fidesui/react";
import { motion, Reorder } from "framer-motion";
import { Option } from "~/features/common/form/inputs";

const ScrollableListItem = ({
  item,
  draggable,
}: {
  item: Option;
  draggable?: boolean;
}) => (
  <Flex
    direction="row"
    p={2}
    gap={2}
    align="center"
    borderBottom="1px"
    borderColor="gray.200"
    bgColor="white"
  >
    {draggable ? <DragHandleIcon /> : null}
    <Text>{item.label}</Text>
  </Flex>
);

const ScrollableList = ({
  values,
  draggable,
  onReorder,
}: {
  values: Option[];
  draggable?: boolean;
  onReorder: (newOrder: Option[]) => void;
}) => {
  return draggable ? (
    <Box
      as={motion.div}
      layoutScroll
      borderRadius="md"
      border="1px"
      borderColor="gray.200"
      maxH={48}
      overflowY="scroll"
    >
      <List as={Reorder.Group} values={values} onReorder={onReorder}>
        {values.map((opt) => (
          <Reorder.Item
            key={opt.value}
            value={opt}
            whileDrag={{ borderTop: "1px solid #E2E8DE" }}
          >
            <ScrollableListItem item={opt} draggable />
          </Reorder.Item>
        ))}
      </List>
    </Box>
  ) : (
    <Box
      borderRadius="md"
      border="1px"
      borderColor="gray.200"
      maxH={48}
      overflowY="scroll"
    >
      <List>
        {values.map((opt) => (
          <ScrollableListItem item={opt} />
        ))}
      </List>
    </Box>
  );
};

export default ScrollableList;
