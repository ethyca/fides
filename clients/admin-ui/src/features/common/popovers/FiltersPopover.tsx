import { AntButton, AntPopover, CloseIcon, PopoverProps } from "fidesui";

interface FiltersPopoverProps extends PopoverProps {
  children: React.ReactNode;
  title: string;
}

export interface FilterOption {}

const FiltersPopover = ({
  children,
  trigger = "click",
  placement = "bottomRight",
  title = "Filters",
  ...otherAntPopoverProps
}: FiltersPopoverProps) => {
  return (
    <AntPopover
      content={<h1>asdas</h1>}
      trigger={trigger}
      placement={placement}
      title={
        <div className="flex min-w-[290px] items-center justify-between">
          <AntButton size="small">Reset</AntButton>
          <span>{title}</span>
          <CloseIcon />
        </div>
      }
      {...otherAntPopoverProps}
    >
      {children}
    </AntPopover>
  );
};
export default FiltersPopover;
