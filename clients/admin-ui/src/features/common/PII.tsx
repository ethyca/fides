type PIIProps = {
  data: string;
  revealPII: boolean;
};

const PII = ({ data, revealPII }: PIIProps) => {
  const pii = revealPII ? data : data.replace(/./g, "*");
  return (
    // eslint-disable-next-line react/jsx-no-useless-fragment
    <>{pii}</>
  );
};

export default PII;
