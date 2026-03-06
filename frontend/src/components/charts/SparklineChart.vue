<script setup lang="ts">
import {
  CategoryScale,
  Chart as ChartJS,
  type ChartDataset,
  type ChartData,
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

const props = withDefaults(
  defineProps<{
    measurements: StationMeasurement[];
    limit?: number;
  }>(),
  {
    limit: undefined,
  },
);

const labels = computed(() => {
  return props.measurements.map((row) => row.timestamp);
});

const values = computed(() => {
  return props.measurements.map((row) => row.value);
});

const parseIsoLabel = (value: string): DateTime | null => {
  const parsed = DateTime.fromISO(value);
  return parsed.isValid ? parsed : null;
};

const gridColorForIsoLabel = (isoLabel: string): string => {
  const parsed = parseIsoLabel(isoLabel);
  if (!parsed) {
    return "transparent";
  }

  if (parsed.hour === 0 && parsed.minute === 0) {
    return "hsla(205, 31%, 55%, 0.55)";
  }

  if (parsed.hour === 12 && parsed.minute === 0) {
    return "hsla(205, 31%, 55%, 0.3)";
  }

  return "transparent";
};

const tooltipTitleForIsoLabel = (isoLabel: string): string => {
  const parsed = parseIsoLabel(isoLabel);
  if (!parsed) {
    return isoLabel;
  }
  return parsed.setLocale("de").toFormat("dd.LL.yyyy HH:mm");
};

const chartData = computed<ChartData<"line">>(() => {
  const datasets: ChartDataset<"line">[] = [
    {
      label: "Measured level",
      data: values.value,
      borderColor: "hsl(195 90% 38%)",
      backgroundColor: "hsla(195, 90%, 38%, 0.16)",
      pointRadius: 0,
      tension: 0.35,
      fill: true,
      borderWidth: 2,
    },
  ];

  if (typeof props.limit === "number") {
    datasets.push({
      label: "Limit",
      data: labels.value.map(() => props.limit as number),
      borderColor: "hsla(0, 82%, 55%, 0.9)",
      borderDash: [5, 4],
      borderWidth: 1.5,
      pointRadius: 0,
      fill: false,
      tension: 0,
    });
  }

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
    plugins: {
      legend: { display: false },
      tooltip: {
        enabled: true,
        intersect: false,
        mode: "index",
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
              return item.dataset.label ?? "";
            }
            return `${item.dataset.label}: ${Math.round(y)} cm`;
          },
        },
      },
    },
    scales: {
      x: {
        display: true,
        offset: false,
        grid: {
          drawTicks: false,
          color: (context) => {
            const label = String(context.tick?.label ?? "");
            return gridColorForIsoLabel(label);
          },
          lineWidth: (context) => {
            const label = String(context.tick?.label ?? "");
            const parsed = parseIsoLabel(label);
            if (!parsed) {
              return 0;
            }
            if (parsed.hour === 0 && parsed.minute === 0) {
              return 1.2;
            }
            if (parsed.hour === 12 && parsed.minute === 0) {
              return 0.8;
            }
            return 0;
          },
        },
        ticks: {
          display: false,
          autoSkip: false,
          maxRotation: 0,
          minRotation: 0,
        },
      },
      y: {
        display: false,
      },
    },
    elements: {
      line: {
        capBezierPoints: true,
      },
    },
  };
});
</script>

<template>
  <div
    class="sparkline-chart"
    role="img"
    aria-label="Pegel history last 3 days"
  >
    <Line
      v-if="measurements.length > 0"
      :data="chartData"
      :options="chartOptions"
    />
    <div v-else class="h-full rounded bg-muted/30" />
  </div>
</template>

<style scoped>
.sparkline-chart {
  height: 56px;
  width: 100%;
  min-width: 0;
  overflow: hidden;
}

.sparkline-chart :deep(canvas) {
  display: block;
  width: 100% !important;
  max-width: 100% !important;
}

@media (min-width: 768px) {
  .sparkline-chart {
    height: 72px;
  }
}
</style>
