import { useMemo } from 'react';
import type { EChartsOption } from 'echarts';

import type { HistoryPoint } from '../types/data';
import { EChart } from './EChart';

interface HistoryChartProps {
  points: HistoryPoint[];
  metric: 'hype_score' | 'attention_score' | 'volume_ratio_30d';
  title: string;
}

export function HistoryChart({ points, metric, title }: HistoryChartProps) {
  const option = useMemo<EChartsOption>(() => {
    const filtered = points.filter((point) => point[metric] !== null);
    return {
      tooltip: { trigger: 'axis' },
      grid: { left: 18, right: 18, top: 24, bottom: 25, containLabel: true },
      xAxis: {
        type: 'category',
        data: filtered.map((point) => point.date),
        boundaryGap: false,
        axisLabel: { color: '#8497b5', hideOverlap: true },
        axisLine: { lineStyle: { color: 'rgba(132, 151, 181, .2)' } },
      },
      yAxis: {
        type: 'value',
        min: metric === 'volume_ratio_30d' ? undefined : 0,
        max: metric === 'volume_ratio_30d' ? undefined : 100,
        axisLabel: { color: '#8497b5' },
        splitLine: { lineStyle: { color: 'rgba(132, 151, 181, .12)' } },
      },
      series: [{
        type: 'line',
        data: filtered.map((point) => point[metric]),
        smooth: 0.28,
        symbol: 'circle',
        symbolSize: filtered.length < 8 ? 6 : 3,
        lineStyle: { width: 2.5, color: '#65a2ff' },
        itemStyle: { color: '#9bc3ff' },
        areaStyle: { color: 'rgba(80, 137, 255, .10)' },
        connectNulls: false,
      }],
    };
  }, [metric, points]);

  return <EChart option={option} height={300} ariaLabel={title} />;
}
