import React from "react";
import { Box, Heading, Stack } from "@fidesui/react";
import { useSelectedHistory } from "./SelectedHistoryContext";
import _ from "lodash";

const SystemDataGroup = ({
  heading,
  children,
}: {
  heading: string;
  children?: React.ReactNode;
}) => {
  const { selectedHistory } = useSelectedHistory();
  const childArray = React.Children.toArray(children);

  // Filter children based on whether their name prop exists in before or after of selectedHistory
  const filteredChildren = childArray.filter((child) => {
    if (React.isValidElement(child) && child.props.name) {
      const name = child.props.name;
      const beforeValue = _.get(selectedHistory?.before, name);
      const afterValue = _.get(selectedHistory?.after, name);
      return !_.isEmpty(beforeValue) || !_.isEmpty(afterValue);
    }
    return false;
  });

  // If no children should be rendered, return null
  if (filteredChildren.length === 0) {
    return null;
  }

  return (
    <Stack marginTop="0px !important">
      <Box
        maxWidth="720px"
        border="1px"
        borderColor="gray.200"
        borderRadius={6}
        overflow="visible"
        mt={6}
      >
        <Box
          backgroundColor="gray.50"
          px={6}
          py={4}
          display="flex"
          flexDirection="row"
          alignItems="center"
          borderBottom="1px"
          borderColor="gray.200"
          borderTopRadius={6}
        >
          <Heading as="h3" size="xs">
            {heading}
          </Heading>
        </Box>

        <Stack>{filteredChildren}</Stack>
      </Box>
    </Stack>
  );
};

export default SystemDataGroup;
