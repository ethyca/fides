import { Icons, Tooltip, TooltipProps } from "fidesui";

interface InfoTooltipProps extends Omit<TooltipProps, "children" | "title"> {
  label: string | null | undefined;
}

export const InfoTooltip = ({ label, ...props }: InfoTooltipProps) =>
  label ? (
    <Tooltip
      title={label}
      trigger={["hover", "focus"]}
      placement="right"
      {...props}
    >
      <span
        style={{ color: "var(--fidesui-neutral-200)", display: "inline-block" }}
        // eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex -- popover makes it interactive
        tabIndex={0}
      >
        {/* ViewBox is set to match the size of the icon (default 16px) with 1px padding all around */}
        <Icons.InformationFilled viewBox="0 -1 34 34" />
      </span>
    </Tooltip>
  ) : null;
