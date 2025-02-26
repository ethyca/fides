import {
  AntButton as Button,
  AntButtonProps as ButtonProps,
  Tooltip,
  useClipboard,
} from "fidesui";
import React, { useState } from "react";

import { CopyIcon } from "./Icon";

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
      label={tooltipText}
      placement="top"
      closeDelay={500}
      onOpen={() => {
        setTooltipText(TooltipText.COPY);
      }}
      onClose={() => {
        setTooltipText(TooltipText.COPY);
      }}
    >
      <Button
        icon={<CopyIcon />}
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
