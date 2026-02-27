import {
  Button,
  Flex,
  Modal,
  Space,
  Switch,
  Text,
  Tooltip,
  useMessage,
} from "fidesui";
import { useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { selectToken } from "~/features/auth/auth.slice";

import { PrivacyAssessmentDetailResponse } from "./types";

interface ReportModalProps {
  assessment: PrivacyAssessmentDetailResponse;
  isComplete: boolean;
  open: boolean;
  onClose: () => void;
}

export const ReportModal = ({
  assessment,
  isComplete,
  open,
  onClose,
}: ReportModalProps) => {
  const message = useMessage();
  const token = useAppSelector(selectToken);

  // Default to compliance format when complete, internal otherwise
  const [isComplianceFormat, setIsComplianceFormat] = useState(isComplete);
  const [isDownloading, setIsDownloading] = useState(false);

  const handleClose = () => {
    setIsComplianceFormat(isComplete);
    onClose();
  };

  const handleDownload = async () => {
    if (!assessment?.id) {
      return;
    }

    setIsDownloading(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_FIDESCTL_API;
      const exportMode = isComplianceFormat ? "external" : "internal";
      const response = await fetch(
        `${baseUrl}/plus/privacy-assessments/${assessment.id}/pdf?export_mode=${exportMode}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      if (!response.ok) {
        message.error("Failed to download PDF. Please try again.");
        return;
      }

      // Extract filename from Content-Disposition header
      const contentDisposition = response.headers.get("content-disposition");
      let filename = `privacy_assessment_${assessment.id}.pdf`;
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?([^"]+)"?/);
        if (match) {
          [, filename] = match;
        }
      }

      // Download the PDF
      const arrayBuffer = await response.arrayBuffer();
      const blob = new Blob([arrayBuffer], {
        type: response.headers.get("content-type") || "application/pdf",
      });
      const fileSaver = await import("file-saver");
      const saveAs = fileSaver.saveAs || fileSaver.default;
      saveAs(blob, filename);

      message.success("PDF downloaded successfully");
      handleClose();
    } catch {
      message.error("Failed to download PDF. Please try again.");
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <Modal
      title="Generate Report"
      open={open}
      onCancel={handleClose}
      footer={
        <Flex justify="flex-end" gap="small">
          <Button onClick={handleClose}>Cancel</Button>
          <Button
            type="primary"
            onClick={handleDownload}
            loading={isDownloading}
          >
            {isDownloading ? "Generating..." : "Download PDF"}
          </Button>
        </Flex>
      }
      width={500}
    >
      <Space direction="vertical" size="middle" className="w-full py-4">
        <Text strong className="text-xs uppercase tracking-wide text-gray-500">
          Export Format
        </Text>
        <Flex align="center" gap="middle">
          <Tooltip
            title={
              !isComplete
                ? "Assessment must be 100% complete to enable Compliance Documentation Format"
                : undefined
            }
          >
            <Switch
              checked={isComplianceFormat}
              disabled={!isComplete}
              onChange={setIsComplianceFormat}
            />
          </Tooltip>
          <Tooltip
            title={
              isComplianceFormat
                ? "Excludes executive summary, risk assessment, and supporting evidence"
                : "Includes executive summary, risk assessment, and supporting evidence"
            }
          >
            <Text className="cursor-help">
              {isComplianceFormat
                ? "Compliance Documentation Format"
                : "Internal Format"}
            </Text>
          </Tooltip>
        </Flex>
      </Space>
    </Modal>
  );
};
