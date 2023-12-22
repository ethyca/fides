import { Box } from '@fidesui/react';
import React from 'react';
import Plot from 'react-plotly.js';

interface FileTypeData {
    fileType: string;
    percentage: number;
}

interface DonutChartProps {
    data: FileTypeData[];
}

const ethycaColors = [
    "#C1A7F9",
    "#824EF2",
    "#FAF5FF",
    "#2D3748",
    "#E2E8F0",
    "#B794F4",

];

const DonutChart: React.FC<DonutChartProps> = ({ data }) => {
    const chartData = {
        labels: data.map((item) => item.fileType),
        values: data.map((item) => item.percentage),
        type: 'pie',
        hole: 0.3,
        hoverinfo: 'label+percent',
        marker: {
            colors: ethycaColors
        },
    };

    return (
        <Box>
            <Plot
                data={[chartData]}
                layout={{
                    xaxis: {
                        title: 'Percentage',
                        tickformat: '%',
                    },
                    yaxis: {
                        title: 'File Types',
                    },
                    margin: { "t": 0, "b": 20, "l": 0, "r": 0 },
                }}
                config={{ responsive: true, displayModeBar: false }}
                style={{ width: '100%', height: '200px' }}
            />
        </Box>
    );
};

export default DonutChart;
