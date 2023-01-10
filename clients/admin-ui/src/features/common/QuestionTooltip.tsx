import { Tooltip, TooltipProps } from "@chakra-ui/react";
// import { Tooltip } from "@fidesui/react";
import { QuestionIcon } from "@fidesui/react";

const QuestionTooltip = ({ ...props }: Omit<TooltipProps, "children">) => (
  <Tooltip placement="right" {...props}>
    <QuestionIcon color="gray.400" />
  </Tooltip>
);

export default QuestionTooltip;
