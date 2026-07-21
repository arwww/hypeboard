import { useMemo } from 'react';
import type { EChartsOption } from 'echarts';

import type { LatestSymbol } from '../types/data';
import { EChart } from './EChart';

export function ScoreComposition({ stock }: { stock: LatestSymbol }) {
  const option = useMemo<EChartsOption>(() => ({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 8, right: 20, top: 12, bottom: 8, containLabel: true },
    xAxis: {
      type: 'value',
      min: 0,
      max: 100,
      splitLine: { lineStyle: { color: 'rgba(132, 151, 181, .12)' } },
      axisLabel: { color: '#8ea0bc' },
    },
    yAxis: {
      type: 'category',
      data: ['Impact', 'Retail proxy', 'Trading', 'Attention'],
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#b9c7dc' },
    },
    series: [{
      type: 'bar',
      data: [stock.impact_score, stock.retail_proxy_score, stock.trading_score, stock.attention_score],
      barWidth: 16,
      itemStyle: { borderRadius: [0, 5, 5, 0], color: '#5e8bff' },
      label: {
        show: true,
        position: 'right',
        color: '#dce8fa',
        formatter: (params) => params.value == null ? 'N/A' : Math.round(Number(params.value)).toString(),
      },
    }],
  }), [stock]);

  return <EChart option={option} height={260} ariaLabel={`Score composition for ${stock.symbol}`} />;
}
