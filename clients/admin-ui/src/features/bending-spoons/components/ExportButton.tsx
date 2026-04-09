import { Button } from "fidesui";
import { toPng } from "html-to-image";
import type { RefObject } from "react";
import { useCallback } from "react";

interface ExportButtonProps {
  targetRef: RefObject<HTMLDivElement | null>;
  filename: string;
  backgroundColor?: string;
}

const ExportButton = ({
  targetRef,
  filename,
  backgroundColor,
}: ExportButtonProps) => {
  const handleExport = useCallback(async () => {
    if (!targetRef.current) return;
    const dataUrl = await toPng(targetRef.current, {
      ...(backgroundColor ? { backgroundColor } : {}),
      pixelRatio: 2,
    });
    const link = document.createElement("a");
    link.download = `${filename}.png`;
    link.href = dataUrl;
    link.click();
  }, [targetRef, filename, backgroundColor]);

  return (
    <Button type="default" size="small" onClick={handleExport}>
      Download PNG
    </Button>
  );
};

export default ExportButton;
