<script setup lang="ts">
import { useQuery } from "@tanstack/vue-query";
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import Alert from "@/components/ui/alert/Alert.vue";
import Badge from "@/components/ui/badge/Badge.vue";
import Button from "@/components/ui/button/Button.vue";
import Card from "@/components/ui/card/Card.vue";
import CardContent from "@/components/ui/card/CardContent.vue";
import CardHeader from "@/components/ui/card/CardHeader.vue";
import CardTitle from "@/components/ui/card/CardTitle.vue";
import SparklineChart from "@/components/charts/SparklineChart.vue";
import { ApiError } from "@/api/client";
import { useFormatters } from "@/composables/useFormatters";
import { getJobStatus, listJobs } from "@/features/jobs/api";
import type { JobStatus } from "@/features/jobs/types";
import { listStationMeasurements, listStations } from "@/features/stations/api";
import type { StationMeasurement } from "@/features/stations/types";

const { t, te } = useI18n();
const { formatDateTime, formatNumber } = useFormatters();
const router = useRouter();

const jobsQuery = useQuery({
  queryKey: ["dashboard", "jobs"],
  queryFn: () => listJobs(false),
});

const jobs = computed(() => jobsQuery.data.value ?? []);
const stationUuids = computed(() =>
  Array.from(
    new Set(jobs.value.map((job) => job.station_uuid).filter(Boolean)),
  ),
);

const stationsQuery = useQuery({
  queryKey: computed(() => ["dashboard", "stations", stationUuids.value]),
  queryFn: () =>
    listStations({
      uuids: stationUuids.value,
      limit: stationUuids.value.length || 1,
      offset: 0,
    }),
  enabled: computed(() => stationUuids.value.length > 0),
  staleTime: 5 * 60 * 1000,
});

const statusQuery = useQuery({
  queryKey: computed(() => [
    "dashboard",
    "status",
    jobs.value.map((job) => job.job_uuid),
  ]),
  queryFn: async () => {
    const pairs = await Promise.all(
      jobs.value.map(async (job) => {
        try {
          const status = await getJobStatus(job.job_uuid);
          return [job.job_uuid, status] as const;
        } catch {
          return [job.job_uuid, null] as const;
        }
      }),
    );

    return Object.fromEntries(pairs) as Record<string, JobStatus | null>;
  },
  enabled: computed(() => jobs.value.length > 0),
  staleTime: 60 * 1000,
});

const measurementsQuery = useQuery({
  queryKey: computed(() => ["dashboard", "measurements", stationUuids.value]),
  queryFn: async () => {
    const pairs = await Promise.all(
      stationUuids.value.map(async (stationUuid) => {
        try {
          const measurements = await listStationMeasurements(
            stationUuid,
            "P3D",
          );
          return [stationUuid, measurements] as const;
        } catch {
          return [stationUuid, []] as const;
        }
      }),
    );

    return Object.fromEntries(pairs) as Record<string, StationMeasurement[]>;
  },
  enabled: computed(() => stationUuids.value.length > 0),
  staleTime: 2 * 60 * 1000,
  refetchInterval: 2 * 60 * 1000,
});

const stationsByUuid = computed(() => {
  const map = new Map<string, { label: string; detail: string }>();

  for (const station of stationsQuery.data.value?.items ?? []) {
    const water = station.water_longname || station.water_shortname;
    const label = water ? `${station.shortname} - ${water}` : station.shortname;
    const detail = [station.agency, station.uuid].filter(Boolean).join(" | ");
    map.set(station.uuid, { label, detail });
  }

  return map;
});

const activeJobsCount = computed(
  () => jobs.value.filter((job) => job.enabled).length,
);

const dashboardError = computed(() => {
  const error = jobsQuery.error.value;
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return t("dashboard.loadFailed");
});

const getStatusLabel = (jobUuid: string): string => {
  const rawState = statusQuery.data.value?.[jobUuid]?.state;
  if (!rawState) {
    return t("dashboard.statusUnknown");
  }

  const token = rawState
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
  const key = `dashboard.stateValues.${token}`;
  return token && te(key) ? t(key) : rawState;
};

const getLastUpdatedLabel = (jobUuid: string, fallback: string): string => {
  const value = statusQuery.data.value?.[jobUuid]?.updated_at || fallback;
  return formatDateTime(value);
};

const getMeasurements = (stationUuid: string): StationMeasurement[] => {
  return measurementsQuery.data.value?.[stationUuid] ?? [];
};

const getLatestMeasurement = (stationUuid: string): number | null => {
  const measurements = getMeasurements(stationUuid);
  if (measurements.length === 0) {
    return null;
  }
  return measurements[measurements.length - 1].value;
};
</script>

<template>
  <section class="space-y-4">
    <Card>
      <CardContent class="py-5">
        <div
          class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between"
        >
          <div>
            <p
              class="text-xs font-semibold uppercase tracking-wide text-muted-foreground"
            >
              {{ t("dashboard.kicker") }}
            </p>
            <h2 class="text-xl font-semibold">{{ t("dashboard.title") }}</h2>
            <p class="text-sm text-muted-foreground">
              {{
                t("dashboard.subtitle", {
                  total: formatNumber(jobs.length),
                  active: formatNumber(activeJobsCount),
                })
              }}
            </p>
          </div>
          <div class="flex flex-wrap gap-2">
            <Button
              size="sm"
              variant="outline"
              @click="router.push({ name: 'jobs' })"
              >{{ t("dashboard.actions.openJobs") }}</Button
            >
            <Button size="sm" @click="router.push({ name: 'job-create' })">{{
              t("dashboard.actions.newJob")
            }}</Button>
          </div>
        </div>
      </CardContent>
    </Card>

    <Alert v-if="jobsQuery.isError.value" variant="destructive">{{
      dashboardError
    }}</Alert>

    <div
      v-if="jobsQuery.isLoading.value"
      class="rounded-md border bg-muted/30 p-4 text-sm text-muted-foreground"
    >
      {{ t("dashboard.loading") }}
    </div>

    <div
      v-else-if="jobs.length === 0"
      class="rounded-md border bg-muted/30 p-4 text-sm text-muted-foreground"
    >
      {{ t("dashboard.empty") }}
    </div>

    <div v-else class="grid gap-4 lg:grid-cols-2">
      <Card v-for="job in jobs" :key="job.job_uuid" class="min-w-0 border-border/80">
        <CardHeader>
          <div class="flex items-start justify-between gap-3">
            <div>
              <CardTitle class="text-lg">{{ job.name }}</CardTitle>
              <p class="mt-1 text-xs text-muted-foreground">
                {{
                  stationsByUuid.get(job.station_uuid)?.label ||
                  job.station_uuid
                }}
              </p>
            </div>
            <Badge :variant="job.enabled ? 'default' : 'secondary'">{{
              job.enabled ? t("dashboard.enabled") : t("dashboard.disabled")
            }}</Badge>
          </div>
        </CardHeader>
        <CardContent class="space-y-3">
          <div
            class="grid grid-cols-1 gap-2 rounded-md border bg-muted/25 p-3 text-xs text-muted-foreground sm:grid-cols-2"
          >
            <p>
              <span class="block text-[10px] uppercase tracking-wide">{{
                t("dashboard.job.station")
              }}</span>
                <span class="text-sm text-foreground break-all">{{
                  stationsByUuid.get(job.station_uuid)?.detail || job.station_uuid
                }}</span>
            </p>
            <p>
              <span class="block text-[10px] uppercase tracking-wide">{{
                t("dashboard.job.limit")
              }}</span>
              <span class="text-sm text-foreground"
                >{{ formatNumber(job.limit_cm) }} cm</span
              >
            </p>
            <p>
              <span class="block text-[10px] uppercase tracking-wide">{{
                t("dashboard.job.state")
              }}</span>
              <span class="text-sm text-foreground">{{
                getStatusLabel(job.job_uuid)
              }}</span>
            </p>
            <p>
              <span class="block text-[10px] uppercase tracking-wide">{{
                t("dashboard.job.updated")
              }}</span>
              <span class="text-sm text-foreground">{{
                getLastUpdatedLabel(job.job_uuid, job.updated_at)
              }}</span>
            </p>
          </div>

          <div class="space-y-2 rounded-md border bg-card p-2">
            <p
              class="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground"
            >
              {{ t("dashboard.job.trend") }}
            </p>
            <SparklineChart
              :measurements="getMeasurements(job.station_uuid)"
              :limit="job.limit_cm"
            />
            <p class="text-xs text-muted-foreground">
              {{
                getLatestMeasurement(job.station_uuid) !== null
                  ? t("dashboard.job.latestValue", {
                      value: formatNumber(
                        getLatestMeasurement(job.station_uuid) || 0,
                      ),
                    })
                  : t("dashboard.job.noRecentData")
              }}
            </p>
          </div>

          <div class="flex flex-wrap justify-end gap-2">
            <Button
              size="sm"
              variant="outline"
              @click="
                router.push({
                  name: 'job-details',
                  params: { jobUuid: job.job_uuid },
                })
              "
              >{{ t("dashboard.actions.view") }}</Button
            >
            <Button
              size="sm"
              variant="outline"
              @click="
                router.push({
                  name: 'job-edit',
                  params: { jobUuid: job.job_uuid },
                })
              "
              >{{ t("dashboard.actions.edit") }}</Button
            >
          </div>
        </CardContent>
      </Card>
    </div>

    <p class="text-xs text-muted-foreground">
      {{ t("dashboard.dataSource") }}
      <a
        class="font-semibold text-foreground hover:underline"
        href="https://pegelonline.wsv.de"
        target="_blank"
        rel="noreferrer"
        >Pegelonline</a
      >
    </p>
  </section>
</template>
