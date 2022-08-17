import { Icon, Tooltip, useClipboard } from "@fidesui/react";
import React, { useState } from "react";

enum TooltipText {
  COPY = "Copy",
  COPIED = "Copied",
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

type ClipboardButtonProps = {
  copyText: string;
};

const ClipboardButton = ({ copyText }: ClipboardButtonProps) => {
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
      <Icon
        cursor="pointer"
        width={18}
        height={18}
        viewBox="0 0 18 18"
        color={iconColor}
        onClick={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        <path
          fill="currentColor"
          d="M15 3.75V0H10.625C9.58945 0 8.75 0.839453 8.75 1.875V13.125C8.75 14.1605 9.58945 15 10.625 15H18.125C19.1605 15 20 14.1605 20 13.125V5H16.2852C15.5625 5 15 4.4375 15 3.75ZM16.25 0V3.75H20L16.25 0ZM7.5 13.75V5H1.875C0.839453 5 0 5.83945 0 6.875V18.125C0 19.1605 0.839453 20 1.875 20H9.375C10.4105 20 11.25 19.1605 11.25 18.125V16.25H10C8.62109 16.25 7.5 15.1289 7.5 13.75Z"
        />
      </Icon>
    </Tooltip>
  );
};

export default ClipboardButton;
