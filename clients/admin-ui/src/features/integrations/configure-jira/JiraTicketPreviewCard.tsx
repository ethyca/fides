import { Card, Descriptions } from "fidesui";

interface JiraTicketPreviewData {
  project_key: string;
  issue_type: string;
  summary: string;
  description: string;
  due_date?: string;
}

interface JiraTicketPreviewCardProps {
  data: JiraTicketPreviewData;
}

const JiraTicketPreviewCard = ({ data }: JiraTicketPreviewCardProps) => (
  <Card title="Ticket Preview" size="small" style={{ marginTop: 12 }}>
    <Descriptions column={1} size="small">
      <Descriptions.Item label="Project">{data.project_key}</Descriptions.Item>
      <Descriptions.Item label="Issue type">
        {data.issue_type}
      </Descriptions.Item>
      <Descriptions.Item label="Summary">{data.summary}</Descriptions.Item>
      <Descriptions.Item label="Description">
        <div style={{ whiteSpace: "pre-wrap" }}>{data.description}</div>
      </Descriptions.Item>
      {data.due_date && (
        <Descriptions.Item label="Due date">
          {data.due_date}
        </Descriptions.Item>
      )}
    </Descriptions>
  </Card>
);

export default JiraTicketPreviewCard;
