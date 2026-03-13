<script setup lang="ts">
import {
  CategoryScale,
  Chart as ChartJS,
  type ChartData,
  type ChartDataset,
  type ChartOptions,
  Filler,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
} from "chart.js";
import { computed } from "vue";
import { Line } from "vue-chartjs";
import { DateTime } from "luxon";
import type { StationMeasurement } from "@/features/stations/types";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Filler,
);

const props = defineProps<{
  measurements: StationMeasurement[];
  forecast: StationMeasurement[];
  limit: number;
}>();

const labels = computed(() => {
  const merged = new Set<string>();
  for (const row of props.measurements) {
    merged.add(row.timestamp);
  }
  for (const row of props.forecast) {
    merged.add(row.timestamp);
  }
  return Array.from(merged).sort((a, b) => a.localeCompare(b));
});

const measuredLookup = computed(() => {
  const table = new Map<string, number>();
  for (const row of props.measurements) {
    table.set(row.timestamp, row.value);
  }
  return table;
});

const forecastLookup = computed(() => {
  const table = new Map<string, number>();
  for (const row of props.forecast) {
    table.set(row.timestamp, row.value);
  }
  return table;
});

const measuredValues = computed<(number | null)[]>(() => {
  return labels.value.map((label) => measuredLookup.value.get(label) ?? null);
});

const forecastValues = computed<(number | null)[]>(() => {
  return labels.value.map((label) => forecastLookup.value.get(label) ?? null);
});

const hasSeries = computed(() => labels.value.length > 0);

const parseIsoLabel = (value: string): DateTime | null => {
  const parsed = DateTime.fromISO(value);
  return parsed.isValid ? parsed : null;
};

const tooltipTitleForIsoLabel = (isoLabel: string): string => {
  const parsed = parseIsoLabel(isoLabel);
  if (!parsed) {
    return isoLabel;
  }
  return parsed.setLocale("de").toFormat("dd.LL.yyyy HH:mm");
};

const crossingColor = (
  first: number | null,
  second: number | null,
  limit: number,
  lowColor: string,
  highColor: string,
): string => {
  if (typeof first !== "number" || typeof second !== "number") {
    return lowColor;
  }
  return first >= limit || second >= limit ? highColor : lowColor;
};

const chartData = computed<ChartData<"line">>(() => {
  const datasets: ChartDataset<"line">[] = [
    {
      label: "Measured",
      data: measuredValues.value,
      borderColor: "hsl(206 64% 38%)",
      backgroundColor: "hsla(206, 64%, 38%, 0.1)",
      pointRadius: 0,
      borderWidth: 2,
      tension: 0.3,
      fill: false,
      spanGaps: false,
      segment: {
        borderColor: (ctx) =>
          crossingColor(
            ctx.p0.parsed.y,
            ctx.p1.parsed.y,
            props.limit,
            "hsl(206 64% 38%)",
            "hsl(0 82% 45%)",
          ),
      },
    },
    {
      label: "Forecast",
      data: forecastValues.value,
      borderColor: "hsl(195 90% 38%)",
      pointRadius: 0,
      borderWidth: 2,
      tension: 0.3,
      fill: false,
      borderDash: [6, 5],
      spanGaps: false,
      segment: {
        borderColor: (ctx) =>
          crossingColor(
            ctx.p0.parsed.y,
            ctx.p1.parsed.y,
            props.limit,
            "hsl(195 90% 38%)",
            "hsl(0 82% 45%)",
          ),
      },
    },
    {
      label: "Limit",
      data: labels.value.map(() => props.limit),
      borderColor: "hsla(0, 82%, 45%, 0.85)",
      pointRadius: 0,
      borderWidth: 1.5,
      tension: 0,
      fill: false,
      borderDash: [4, 4],
      spanGaps: true,
    },
  ];

  return {
    labels: labels.value,
    datasets,
  };
});

const chartOptions = computed<ChartOptions<"line">>(() => {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    interaction: {
      mode: "index",
      intersect: false,
    },
    plugins: {
      legend: {
        display: true,
        position: "bottom",
        labels: {
          boxWidth: 18,
          boxHeight: 2,
          usePointStyle: false,
        },
      },
      tooltip: {
        callbacks: {
          title: (items) => {
            const label = items[0]?.label;
            if (!label) {
              return "";
            }
            return tooltipTitleForIsoLabel(label);
          },
          label: (item) => {
            const y = item.parsed.y;
            if (typeof y !== "number") {
              return "";
            }
            return `${item.dataset.label}: ${Math.round(y)} cm`;
          },
        },
      },
    },
    scales: {
      x: {
        display: true,
        ticks: {
          callback: (_value, index) => {
            const label = labels.value[index];
            const parsed = label ? parseIsoLabel(label) : null;
            if (!parsed) {
              return "";
            }
            return parsed.toFormat("dd.LL HH:mm");
          },
          maxTicksLimit: 6,
        },
        grid: {
          color: "hsla(205, 17%, 38%, 0.15)",
        },
      },
      y: {
        display: true,
        title: {
          display: true,
          text: "cm",
        },
        grid: {
          color: "hsla(205, 17%, 38%, 0.12)",
        },
      },
    },
  };
});
</script>

<template>
  <div class="hydrograph-chart" role="img" aria-label="Hydrograph with forecast">
    <Line v-if="hasSeries" :data="chartData" :options="chartOptions" />
    <div v-else class="hydrograph-empty" />
  </div>
</template>

<style scoped>
.hydrograph-chart {
  height: 260px;
  width: 100%;
}

.hydrograph-empty {
  height: 100%;
  border-radius: 0.75rem;
  background: hsl(var(--muted) / 0.4);
}

.hydrograph-chart :deep(canvas) {
  display: block;
  width: 100% !important;
  max-width: 100% !important;
}
</style>
