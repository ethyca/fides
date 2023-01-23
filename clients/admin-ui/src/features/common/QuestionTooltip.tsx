import { QuestionIcon, Tooltip, TooltipProps } from "@fidesui/react";

const QuestionTooltip = ({ ...props }: Omit<TooltipProps, "children">) => (
  <Tooltip placement="right" {...props}>
    <QuestionIcon color="gray.400" />
  </Tooltip>
);

export default QuestionTooltip;
