import {
  AntButton as Button,
  AntCard as Card,
  AntSpace as Space,
  useMessage,
} from "fidesui";

const MessageDemoCard = () => {
  const message = useMessage();

  return (
    <Card title="Toasting" variant="borderless">
      <Space direction="vertical">
        <Button onClick={() => message.success("Success message!")}>
          Success
        </Button>
        <Button onClick={() => message.info("Info message!")}>Info</Button>
        <Button onClick={() => message.warning("Warning message!")}>
          Warning
        </Button>
        <Button onClick={() => message.error("Error message!")}>Error</Button>
        <Button onClick={() => message.loading("Loading...", 2.5)}>
          Loading
        </Button>
      </Space>
    </Card>
  );
};

export default MessageDemoCard;
