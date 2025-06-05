import {
  AntButton as Button,
  AntButtonProps as ButtonProps,
  AntTooltip as Tooltip,
  Icons,
  useClipboard,
} from "fidesui";
import React, { useState } from "react";

enum TooltipText {
  COPY = "Copy",
  COPIED = "Copied!",
}

const useClipboardButton = (copyText: string) => {
  const { onCopy } = useClipboard(copyText);
  const [tooltipText, setTooltipText] = useState(TooltipText.COPY);

  const handleClick = () => {
    setTooltipText(TooltipText.COPIED);
    onCopy();
  };

  return {
    tooltipText,
    handleClick,
    setTooltipText,
  };
};

interface ClipboardButtonProps
  extends Omit<
    ButtonProps,
    "aria-label" | "onClick" | "onMouseUp" | "onMouseEnter" | "onMouseLeave"
  > {
  copyText: string;
}

const ClipboardButton = ({ copyText, ...props }: ClipboardButtonProps) => {
  const { tooltipText, handleClick, setTooltipText } =
    useClipboardButton(copyText);

  return (
    <Tooltip
      title={tooltipText}
      placement="top"
      mouseLeaveDelay={0.5}
      onOpenChange={(value) => {
        setTooltipText(value ? TooltipText.COPY : TooltipText.COPIED);
      }}
    >
      <Button
        icon={<Icons.Copy />}
        aria-label="copy"
        type="text"
        data-testid="clipboard-btn"
        {...props}
        onClick={handleClick}
      />
    </Tooltip>
  );
};

export default ClipboardButton;
