import { Flex, FormControl, FormLabel, Select, Text } from "fidesui";
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
          <FormLabel>Choose Format</FormLabel>
          <Select
            value={downloadType}
            onChange={(e) => setDownloadType(e.target.value as ExportFormat)}
            data-testid="export-format-select"
          >
            <option value={ExportFormat.csv}>CSV</option>
            <option value={ExportFormat.xlsx}>XLSX</option>
          </Select>
        </FormControl>
      </Flex>
    </StandardDialog>
  );
};

export default ReportExportModal;
