import { useState } from "react";

const useClipboardButton = (textToCopy: string) => {
  const [tooltipText, setTooltipText] = useState("Copy");

  const resetTooltipText = () => {
    setTimeout(() => {
      setTooltipText("Copy");
    }, 2000);
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(textToCopy);
      setTooltipText("Copied!");
      resetTooltipText();
    } catch {
      setTooltipText("Copy failed");
      resetTooltipText();
    }
  };
  return { tooltipText, handleCopy };
};

export default useClipboardButton;
