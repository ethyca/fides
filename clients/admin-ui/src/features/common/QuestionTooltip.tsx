import {
  AntTooltip as Tooltip,
  AntTooltipProps as TooltipProps,
  QuestionIcon,
} from "fidesui";

interface QuestionTooltipProps
  extends Omit<TooltipProps, "children" | "title"> {
  label: string | null | undefined;
}

const QuestionTooltip = ({ label, ...props }: QuestionTooltipProps) =>
  label ? (
    <Tooltip title={label} placement="right" {...props}>
      <QuestionIcon color="gray.400" />
    </Tooltip>
  ) : null;

export default QuestionTooltip;
