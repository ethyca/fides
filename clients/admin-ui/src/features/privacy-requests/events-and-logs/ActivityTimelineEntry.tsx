interface ActivityTimelineEntryProps {
  author: string;
  title: string;
  timestamp: string;
  type: string;
  content: string;
}

const ActivityTimelineEntry = ({
  author,
  timestamp,
  title,
  type,
  content,
}: ActivityTimelineEntryProps) => {
  return (
    <div>
      <div>{author}</div>
      <div>{timestamp}</div>
      <div>{title}</div>
      <div>{type}</div>
      <div>{content}</div>
    </div>
  );
};
export default ActivityTimelineEntry;
