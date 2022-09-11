import { Tooltip, TooltipProps } from "@chakra-ui/react";
// import { Tooltip } from "@fidesui/react";
import { QuestionIcon } from "common/Icon";

const QuestionTooltip = ({ ...props }: Omit<TooltipProps, "children">) => (
  <Tooltip {...props}>
    <QuestionIcon color="gray.400" />
  </Tooltip>
);

export default QuestionTooltip;
