import { Box, Grid, Text } from "@fidesui/react";

const ManualSystemFlow = () => (
  <Grid templateColumns="2fr 8fr">
    <Box data-testid="settings">
      <Text>Configuration Settings</Text>
      <Box>
        <Text>Describe</Text>
        <Text>Declare</Text>
        <Text>Review</Text>
      </Box>
    </Box>
    <Box>just a regular form here</Box>
  </Grid>
);

export default ManualSystemFlow;
