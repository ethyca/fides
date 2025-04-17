import {
  AntTooltip as Tooltip,
  AntTooltipProps as TooltipProps,
  QuestionIcon,
} from "fidesui";

interface QuestionTooltipProps
  extends Omit<TooltipProps, "children" | "title"> {
  label: string;
}

const QuestionTooltip = ({ label, ...props }: QuestionTooltipProps) => (
  <Tooltip title={label} placement="right" {...props}>
    <QuestionIcon color="gray.400" />
  </Tooltip>
);

export default QuestionTooltip;
