import {
  AntTooltip as Tooltip,
  AntTypography as Typography,
  Icons,
} from "fidesui";

// Simple attachment interface with only the properties we actually use
interface SimpleAttachment {
  id: string;
  file_name: string;
}

interface AttachmentDisplayProps {
  attachments: SimpleAttachment[];
}

export const AttachmentDisplay = ({ attachments }: AttachmentDisplayProps) => {
  if (!attachments.length) {
    return null;
  }

  // If there's only one attachment, show the filename with tooltip
  if (attachments.length === 1) {
    const attachment = attachments[0];
    return (
      <div
        className="flex flex-wrap gap-2 text-sm text-gray-600"
        data-testid="activity-timeline-attachments"
      >
        <div className="flex items-center">
          <Icons.Attachment className="mr-1 size-4" />
          <Typography.Text
            ellipsis={{ tooltip: true }}
            className="!max-w-[200px]"
          >
            {attachment?.file_name}
          </Typography.Text>
        </div>
      </div>
    );
  }

  // If there are multiple attachments, show "X attachments" with tooltip containing all names
  const tooltipContent = (
    <ul className="list-disc pl-4">
      {attachments.map((attachment) => (
        <li key={attachment.id}>{attachment.file_name}</li>
      ))}
    </ul>
  );

  return (
    <div
      className="flex flex-wrap gap-2 text-sm text-gray-600"
      data-testid="activity-timeline-attachments"
    >
      <div className="flex items-center">
        <Icons.Attachment className="mr-1 size-4" />
        <Tooltip title={tooltipContent}>
          <Typography.Text ellipsis className="!max-w-[200px]">
            {attachments.length} attachments
          </Typography.Text>
        </Tooltip>
      </div>
    </div>
  );
};
