import { TooltipProps } from "@chakra-ui/react";
import { Tooltip } from "@fidesui/react";

import { QuestionIcon } from "./Icon";

const QuestionTooltip = ({ ...props }: Omit<TooltipProps, "children">) => (
  <Tooltip {...props}>
    <QuestionIcon color="gray.400" />
  </Tooltip>
);

export default QuestionTooltip;
