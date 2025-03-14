const ClientMetadata = ({
  title,
  description,
  icon,
}: {
  title: string;
  description: string;
  icon?: string | null;
}) => (
  <>
    <title>{title}</title>
    <meta name="description" content={description} />
    <link rel="icon" href={icon || "/favicon.ico"} />
  </>
);
export default ClientMetadata;
