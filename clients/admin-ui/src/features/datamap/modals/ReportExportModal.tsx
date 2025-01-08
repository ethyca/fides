import {
  AntSelect as Select,
  Flex,
  FormControl,
  FormLabel,
  Text,
} from "fidesui";
import { useState } from "react";

import StandardDialog, {
  StandardDialogProps,
} from "~/features/common/modals/StandardDialog";
import { ExportFormat } from "~/features/datamap/constants";

interface ReportExportModalProps
  extends Omit<StandardDialogProps, "children" | "onConfirm"> {
  onConfirm: (downloadType: ExportFormat) => void;
}

const ReportExportModal = (props: ReportExportModalProps): JSX.Element => {
  const [downloadType, setDownloadType] = useState<ExportFormat>(
    ExportFormat.csv,
  );
  const { onConfirm } = props;

  return (
    <StandardDialog
      heading="Export report"
      continueButtonText="Download"
      size="xl"
      {...props}
      onConfirm={() => onConfirm(downloadType)}
      data-testid="export-modal"
    >
      <Flex direction="column" gap={3} pb={3}>
        <Text textAlign="left">
          Export your data map report using the options below. Depending on the
          number of rows, the file may take a few minutes to process.
        </Text>
        <FormControl>
          <FormLabel htmlFor="format">Choose Format</FormLabel>
          <Select
            id="format"
            value={downloadType}
            onChange={setDownloadType}
            data-testid="export-format-select"
            options={[
              { value: ExportFormat.csv, label: "CSV" },
              { value: ExportFormat.xlsx, label: "XLSX" },
            ]}
            className="w-full"
          />
        </FormControl>
      </Flex>
    </StandardDialog>
  );
};

export default ReportExportModal;
