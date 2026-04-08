import { Avatar, Button, ButtonProps, Icons } from "fidesui";
import { useRouter } from "next/navigation";

/**
 * A back button meant to send the user to the upper level of the nav
 * For example, /consent/privacy-notices/new would go back to /consent/privacy-notices
 * */
const BackButton = ({
  backPath,
  ...props
}: { backPath?: string } & ButtonProps) => {
  const nextRouter = useRouter();
  return (
    <Button
      onClick={backPath ? () => nextRouter.push(backPath) : undefined}
      role={backPath ? "link" : undefined}
      icon={
        <Avatar
          size="small"
          shape="square"
          style={{
            backgroundColor: "var(--fidesui-white)",
            border: "1px solid var(--ant-color-border)",
          }}
        >
          <Icons.ArrowLeft color="var(--fidesui-minos)" />
        </Avatar>
      }
      iconPlacement="start"
      data-testid="back-btn"
      className="mb-6 w-fit px-0"
      type="text"
      {...props}
    >
      Back
    </Button>
  );
};

export default BackButton;
