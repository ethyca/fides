import { Icons, Tooltip, TooltipProps } from "fidesui";

interface InfoTooltipProps extends Omit<TooltipProps, "children" | "title"> {
  label: string | null | undefined;
  size?: number;
}

export const InfoTooltip = ({ label, size, ...props }: InfoTooltipProps) =>
  label ? (
    <Tooltip
      title={label}
      trigger={["hover", "focus"]}
      placement="right"
      {...props}
    >
      <span className="inline-block">
        <Icons.InformationFilled
          color="var(--fidesui-neutral-200)"
          size={size}
        />
      </span>
    </Tooltip>
  ) : null;
