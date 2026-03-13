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
import { useI18n } from "vue-i18n";
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

const { locale, t } = useI18n();

const tokenColor = (token: string, alpha?: number): string => {
  if (typeof document === "undefined") {
    return `hsl(0 0% 40%${typeof alpha === "number" ? ` / ${alpha}` : ""})`;
  }
  const tokenValue = getComputedStyle(document.documentElement)
    .getPropertyValue(token)
    .trim();
  if (!tokenValue) {
    return `hsl(0 0% 40%${typeof alpha === "number" ? ` / ${alpha}` : ""})`;
  }
  return `hsl(${tokenValue}${typeof alpha === "number" ? ` / ${alpha}` : ""})`;
};

const sanitizeSeries = (series: StationMeasurement[]): StationMeasurement[] => {
  const byTimestamp = new Map<string, number>();

  for (const row of series) {
    const value = Number(row.value);
    const timestamp = typeof row.timestamp === "string" ? row.timestamp.trim() : "";
    const ts = Date.parse(timestamp);
    if (!timestamp || !Number.isFinite(ts) || !Number.isFinite(value)) {
      continue;
    }
    byTimestamp.set(timestamp, value);
  }

  return Array.from(byTimestamp.entries())
    .sort((a, b) => Date.parse(a[0]) - Date.parse(b[0]))
    .map(([timestamp, value]) => ({ timestamp, value }));
};

const safeMeasurements = computed(() => sanitizeSeries(props.measurements));
const safeForecast = computed(() => sanitizeSeries(props.forecast));

const labels = computed(() => {
  const merged = new Set<string>();
  for (const row of safeMeasurements.value) {
    merged.add(row.timestamp);
  }
  for (const row of safeForecast.value) {
    merged.add(row.timestamp);
  }
  return Array.from(merged).sort((a, b) => a.localeCompare(b));
});

const measuredLookup = computed(() => {
  const table = new Map<string, number>();
  for (const row of safeMeasurements.value) {
    table.set(row.timestamp, row.value);
  }
  return table;
});

const forecastLookup = computed(() => {
  const table = new Map<string, number>();
  for (const row of safeForecast.value) {
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
  return parsed.setLocale(locale.value).toFormat("dd.LL.yyyy HH:mm");
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
  const measuredBase = tokenColor("--primary");
  const measuredAlert = tokenColor("--destructive");
  const forecastBase = tokenColor("--foreground", 0.78);
  const forecastAlert = tokenColor("--destructive", 0.9);
  const limitColor = tokenColor("--destructive", 0.85);

  const datasets: ChartDataset<"line">[] = [
    {
      label: "Measured",
      data: measuredValues.value,
      borderColor: measuredBase,
      backgroundColor: tokenColor("--primary", 0.1),
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
            measuredBase,
            measuredAlert,
          ),
      },
    },
    {
      label: "Forecast",
      data: forecastValues.value,
      borderColor: forecastBase,
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
            forecastBase,
            forecastAlert,
          ),
      },
    },
    {
      label: "Limit",
      data: labels.value.map(() => props.limit),
      borderColor: limitColor,
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
    datasets: datasets.map((dataset) => ({
      ...dataset,
      label:
        dataset.label === "Measured"
          ? t("charts.hydrograph.measured")
          : dataset.label === "Forecast"
            ? t("charts.hydrograph.forecast")
            : t("charts.hydrograph.limit"),
    })),
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
    locale: locale.value,
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
            return `${item.dataset.label}: ${Math.round(y)} ${t("charts.hydrograph.unitCm")}`;
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
          color: tokenColor("--muted-foreground", 0.16),
        },
      },
      y: {
        display: true,
        title: {
          display: true,
          text: t("charts.hydrograph.unitCm"),
        },
        grid: {
          color: tokenColor("--muted-foreground", 0.13),
        },
      },
    },
  };
});
</script>

<template>
  <div
    class="hydrograph-chart"
    role="img"
    :aria-label="t('charts.hydrograph.ariaLabel')"
  >
    <Line v-if="hasSeries" :data="chartData" :options="chartOptions" />
    <div v-else class="hydrograph-empty" aria-live="polite">
      {{ t("charts.hydrograph.empty") }}
    </div>
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
  display: grid;
  place-items: center;
  padding: 1rem;
  text-align: center;
  font-size: 0.85rem;
  color: hsl(var(--muted-foreground));
  overflow-wrap: anywhere;
}

.hydrograph-chart :deep(canvas) {
  display: block;
  width: 100% !important;
  max-width: 100% !important;
}
</style>
