import { AntTypography as Typography } from "fidesui";

const PrivacyRequestDuplicateDetectionSettings = () => {
  return (
    <div className="max-w-[600px]">
      <Typography.Title level={2} className="!mb-2">
        Duplicate detection
      </Typography.Title>
      <Typography.Paragraph>
        If you enable duplicate detection, Fides will automatically detect and
        label likely duplicate privacy requests. Any request submitted by the
        same email address (or your configured identity field) within the
        configured period of time is automatically labeled with the status of
        &quot;duplicate&quot;.
      </Typography.Paragraph>
    </div>
  );
};

export default PrivacyRequestDuplicateDetectionSettings;
