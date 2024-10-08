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

  const [highlighted, setHighlighted] = useState(false);
  const [tooltipText, setTooltipText] = useState(TooltipText.COPY);

  const handleMouseDown = () => {
    setTooltipText(TooltipText.COPIED);
    onCopy();
  };
  const handleMouseUp = () => {
    setHighlighted(false);
  };

  const handleMouseEnter = () => {
    setHighlighted(true);
  };
  const handleMouseLeave = () => {
    setHighlighted(false);
  };

  return {
    tooltipText,
    highlighted,
    handleMouseDown,
    handleMouseUp,
    handleMouseEnter,
    handleMouseLeave,
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
  const {
    tooltipText,
    highlighted,
    handleMouseDown,
    handleMouseUp,
    handleMouseEnter,
    handleMouseLeave,
    setTooltipText,
  } = useClipboardButton(copyText);

  const iconColor = !highlighted ? "gray.600" : "complimentary.500";

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
        color={iconColor}
        aria-label="copy"
        type="text"
        data-testid="clipboard-btn"
        {...props}
        onClick={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      />
    </Tooltip>
  );
};

export default ClipboardButton;
