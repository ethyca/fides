import { Icons, Popover, PopoverProps } from "fidesui";

interface InfoPopoverProps extends Omit<PopoverProps, "children" | "title"> {
  title: string | null | undefined;
}

export const InfoPopover = ({ title, ...props }: InfoPopoverProps) =>
  title ? (
    <Popover title={title} trigger={["hover", "focus"]} {...props}>
      <span
        style={{ color: "var(--fidesui-neutral-200)", display: "inline-block" }}
        // eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex -- popover makes it interactive
        tabIndex={0}
      >
        {/* ViewBox is set to match the size of the icon (default 16px) with 1px padding all around */}
        <Icons.InformationFilled viewBox="0 -1 34 34" />
      </span>
    </Popover>
  ) : null;
