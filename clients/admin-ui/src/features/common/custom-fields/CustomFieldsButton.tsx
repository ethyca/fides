import { Flex, IconButton, Text } from "@fidesui/react";
import * as React from "react";

import QuestionTooltip from "~/features/common/QuestionTooltip";

import { AddIcon } from "./icons/AddIcon";

type CustomFieldsButtonProps = {
  btnRef: React.MutableRefObject<null>;
  hasTooltip?: boolean;
  onClick: React.MouseEventHandler<HTMLButtonElement>;
};

const CustomFieldsButton: React.FC<CustomFieldsButtonProps> = ({
  btnRef,
  hasTooltip = false,
  onClick,
}) => (
  <Flex alignItems="center" gap="8px">
    <IconButton
      aria-label="Add a custom field"
      data-testid="add-custom-field-btn"
      icon={<AddIcon h="10px" w="10px" />}
      onClick={onClick}
      ref={btnRef}
      size="sm"
      variant="outline"
      _hover={{ cursor: "pointer" }}
    />
    <Text fontWeight="500" fontSize="sm" color="gray.700">
      Add a custom field
    </Text>
    {hasTooltip && <QuestionTooltip label="" />}
  </Flex>
);

export { CustomFieldsButton };
