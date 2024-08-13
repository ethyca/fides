import { QuestionIcon, Tooltip, TooltipProps } from "fidesui";

const QuestionTooltip = ({ ...props }: Omit<TooltipProps, "children">) => (
  <Tooltip placement="right" {...props}>
    <QuestionIcon color="neutral.400" />
  </Tooltip>
);

export default QuestionTooltip;
