const ClientMetadata = ({
  title = "Privacy Center",
  icon,
}: {
  title?: string;
  icon?: string | null;
}) => (
  <>
    <title>{title}</title>
    <link rel="icon" href={icon || "/favicon.ico"} />
  </>
);
export default ClientMetadata;
