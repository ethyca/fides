import { AntTypography as Typography, Icons } from "fidesui";

import { AttachmentResponse } from "~/types/api";

interface AttachmentDisplayProps {
  attachments: AttachmentResponse[];
}

export const AttachmentDisplay = ({ attachments }: AttachmentDisplayProps) => {
  if (!attachments.length) {
    return null;
  }

  return (
    <div
      className="flex flex-wrap gap-2 text-sm text-gray-600"
      data-testid="activity-timeline-attachments"
    >
      {attachments.map((attachment) => (
        <div key={attachment.id} className="flex items-center">
          <Icons.Attachment className="mr-1 size-4" />
          <Typography.Text
            ellipsis={{ tooltip: true }}
            className="!max-w-[200px]"
          >
            {attachment.file_name}
          </Typography.Text>
        </div>
      ))}
    </div>
  );
};
