import { Icon, Tooltip, useClipboard } from '@fidesui/react';
import React, { useState } from 'react';

enum TooltipText {
  COPY = 'Copy',
  COPIED = 'Copied',
}

const useClipboardButton = (requestId: string) => {
  const { onCopy } = useClipboard(requestId);

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
  requestId: string;
};

const ClipboardButton = ({ requestId }: ClipboardButtonProps) => {
  const {
    tooltipText,
    highlighted,
    handleMouseDown,
    handleMouseUp,
    handleMouseEnter,
    handleMouseLeave,
    setTooltipText,
  } = useClipboardButton(requestId);

  const iconColor = !highlighted ? 'gray.600' : 'complimentary.500';

  return (
    <Tooltip
      label={tooltipText}
      placement='top'
      closeDelay={500}
      onOpen={() => {
        setTooltipText(TooltipText.COPY);
      }}
      onClose={() => {
        setTooltipText(TooltipText.COPY);
      }}
    >
      <Icon
        cursor='pointer'
        width={18}
        height={18}
        viewBox='0 0 18 18'
        color={iconColor}
        onClick={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        <path
          fill='currentColor'
          d='M13.7045 2.25H11.8677C11.417 0.942187 10.217 0 8.79545 0C7.37386 0 6.17386 0.942187 5.72386 2.25H3.88636C2.98295 2.25 2.25 3.00516 2.25 3.9375V16.3125C2.25 17.2441 2.98295 18 3.88636 18H13.7045C14.608 18 15.3409 17.2448 15.3409 16.3125V3.9375C15.3409 3.00516 14.608 2.25 13.7045 2.25ZM8.79545 2.25C9.39784 2.25 9.88636 2.75379 9.88636 3.375C9.88636 3.99621 9.39784 4.5 8.79545 4.5C8.19307 4.5 7.70455 3.99727 7.70455 3.375C7.70455 2.75379 8.19205 2.25 8.79545 2.25ZM11.5227 7.875H6.06818C5.76818 7.875 5.52273 7.62188 5.52273 7.3125C5.52273 7.00312 5.76818 6.75 6.06818 6.75H11.5227C11.8227 6.75 12.0682 7.00312 12.0682 7.3125C12.0682 7.62188 11.8227 7.875 11.5227 7.875'
        />
      </Icon>
    </Tooltip>
  );
};

export default ClipboardButton;
