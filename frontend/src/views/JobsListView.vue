<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query";
import Alert from "@/components/ui/alert/Alert.vue";
import Badge from "@/components/ui/badge/Badge.vue";
import Button from "@/components/ui/button/Button.vue";
import Card from "@/components/ui/card/Card.vue";
import CardContent from "@/components/ui/card/CardContent.vue";
import CardHeader from "@/components/ui/card/CardHeader.vue";
import CardTitle from "@/components/ui/card/CardTitle.vue";
import Label from "@/components/ui/label/Label.vue";
import Switch from "@/components/ui/switch/Switch.vue";
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { ApiError } from "@/api/client";
import { useFormatters } from "@/composables/useFormatters";
import { deleteJob, listJobs } from "@/features/jobs/api";
import { listStations } from "@/features/stations/api";

const router = useRouter();
const queryClient = useQueryClient();
const { t } = useI18n();
const { formatNumber } = useFormatters();
const includeDisabled = ref(false);
const infoMessage = ref("");

const jobsQuery = useQuery({
  queryKey: computed(() => ["jobs", includeDisabled.value]),
  queryFn: () => listJobs(includeDisabled.value),
});

const deleteMutation = useMutation({
  mutationFn: deleteJob,
  onSuccess: async () => {
    infoMessage.value = t("jobsList.disabledSuccess");
    await queryClient.invalidateQueries({ queryKey: ["jobs"] });
  },
});

const jobs = computed(() => jobsQuery.data.value ?? []);

const stationUuids = computed(() => {
  return Array.from(
    new Set(jobs.value.map((job) => job.station_uuid).filter(Boolean)),
  );
});

const stationsQuery = useQuery({
  queryKey: computed(() => ["stations", "jobs", stationUuids.value]),
  queryFn: () =>
    listStations({
      uuids: stationUuids.value,
      limit: stationUuids.value.length || 1,
      offset: 0,
    }),
  enabled: computed(() => stationUuids.value.length > 0),
  staleTime: 5 * 60 * 1000,
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

const errorMessage = computed(() => {
  const error = jobsQuery.error.value;
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return t("jobsList.loadFailed");
});

const deleteErrorMessage = computed(() => {
  const error = deleteMutation.error.value;
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "";
});

const goToCreate = () => {
  router.push({ name: "job-create" });
};

const handleDelete = async (jobUuid: string) => {
  const confirmed = window.confirm(t("jobsList.confirmDelete"));
  if (!confirmed) {
    return;
  }

  await deleteMutation.mutateAsync(jobUuid);
};
</script>

<template>
  <section class="jobs-list-view space-y-4">
    <Card class="jobs-list-card">
      <CardHeader>
        <div
          class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between"
        >
          <CardTitle class="text-2xl md:text-3xl">{{ t("jobsList.title") }}</CardTitle>
          <Button @click="goToCreate">{{ t("jobsList.createJob") }}</Button>
        </div>
      </CardHeader>
      <CardContent>
        <div class="mb-4 flex items-center gap-2 text-sm text-muted-foreground">
          <Switch v-model="includeDisabled" input-id="include-disabled" />
          <Label for="include-disabled">{{
            t("jobsList.includeDisabled")
          }}</Label>
        </div>

        <Alert v-if="infoMessage">{{ infoMessage }}</Alert>
        <Alert v-if="jobsQuery.isError.value" variant="destructive">{{
          errorMessage
        }}</Alert>
        <Alert v-if="deleteMutation.isError.value" variant="destructive">{{
          deleteErrorMessage
        }}</Alert>

        <div
          v-if="jobsQuery.isLoading.value"
          class="text-sm text-muted-foreground"
        >
          {{ t("jobsList.loading") }}
        </div>

        <div
          v-else-if="jobs.length === 0"
          class="rounded-md border bg-muted/30 p-4 text-sm text-muted-foreground"
        >
          {{ t("jobsList.empty") }}
        </div>

        <div v-else class="space-y-3 md:hidden">
          <div
            v-for="job in jobs"
            :key="job.job_uuid"
            class="rounded-md border bg-card p-3"
          >
            <div class="flex items-start justify-between gap-2">
              <p class="font-semibold">{{ job.name }}</p>
              <Badge :variant="job.enabled ? 'default' : 'secondary'">{{
                job.enabled ? t("jobsList.enabled") : t("jobsList.disabled")
              }}</Badge>
            </div>
            <p class="mt-1 text-sm text-muted-foreground break-words">
              {{
                stationsByUuid.get(job.station_uuid)?.label || job.station_uuid
              }}
            </p>
            <p class="text-xs text-muted-foreground break-all">
              {{
                stationsByUuid.get(job.station_uuid)?.detail || job.station_uuid
              }}
            </p>

            <div
              class="mt-3 grid grid-cols-2 gap-2 text-xs text-muted-foreground"
            >
              <p>
                <span class="block uppercase tracking-wide">{{
                  t("jobsList.table.limit")
                }}</span>
                <span class="text-sm text-foreground"
                  >{{ formatNumber(job.limit_cm) }} cm</span
                >
              </p>
              <p>
                <span class="block uppercase tracking-wide">{{
                  t("jobsList.table.locale")
                }}</span>
                <span class="text-sm text-foreground">{{ job.locale }}</span>
              </p>
            </div>

            <div class="mt-3 grid grid-cols-3 gap-2">
              <Button
                variant="outline"
                size="sm"
                class="w-full"
                @click="
                  router.push({
                    name: 'job-details',
                    params: { jobUuid: job.job_uuid },
                  })
                "
                >{{ t("jobsList.view") }}</Button
              >
              <Button
                variant="outline"
                size="sm"
                class="w-full"
                @click="
                  router.push({
                    name: 'job-edit',
                    params: { jobUuid: job.job_uuid },
                  })
                "
                >{{ t("jobsList.edit") }}</Button
              >
              <Button
                variant="destructive"
                size="sm"
                class="w-full"
                :disabled="deleteMutation.isPending.value"
                @click="handleDelete(job.job_uuid)"
              >
                {{
                  deleteMutation.isPending.value
                    ? t("jobsList.deleting")
                    : t("jobsList.delete")
                }}
              </Button>
            </div>
          </div>
        </div>

        <div class="hidden overflow-x-auto md:block">
          <table class="w-full min-w-[680px] border-collapse text-left text-sm">
            <thead>
              <tr
                class="border-b text-xs uppercase tracking-[0.12em] text-muted-foreground"
              >
                <th class="py-3 pr-4">{{ t("jobsList.table.name") }}</th>
                <th class="py-3 pr-4">{{ t("jobsList.table.station") }}</th>
                <th class="py-3 pr-4">{{ t("jobsList.table.limit") }}</th>
                <th class="py-3 pr-4">{{ t("jobsList.table.locale") }}</th>
                <th class="py-3 pr-4">{{ t("jobsList.table.status") }}</th>
                <th class="py-3 text-right">
                  {{ t("jobsList.table.actions") }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="job in jobs"
                :key="job.job_uuid"
                class="border-b last:border-none"
              >
                <td class="py-3 pr-4 font-semibold">{{ job.name }}</td>
                <td class="py-3 pr-4">
                  <p class="font-medium">
                    {{
                      stationsByUuid.get(job.station_uuid)?.label ||
                      job.station_uuid
                    }}
                  </p>
                  <p class="text-xs text-muted-foreground break-all">
                    {{
                      stationsByUuid.get(job.station_uuid)?.detail ||
                      job.station_uuid
                    }}
                  </p>
                </td>
                <td class="py-3 pr-4 text-muted-foreground">
                  {{ formatNumber(job.limit_cm) }} cm
                </td>
                <td class="py-3 pr-4 text-muted-foreground">
                  {{ job.locale }}
                </td>
                <td class="py-3 pr-4">
                  <Badge :variant="job.enabled ? 'default' : 'secondary'">{{
                    job.enabled ? t("jobsList.enabled") : t("jobsList.disabled")
                  }}</Badge>
                </td>
                <td class="py-3 text-right">
                  <div class="flex justify-end gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      @click="
                        router.push({
                          name: 'job-details',
                          params: { jobUuid: job.job_uuid },
                        })
                      "
                      >{{ t("jobsList.view") }}</Button
                    >
                    <Button
                      variant="outline"
                      size="sm"
                      @click="
                        router.push({
                          name: 'job-edit',
                          params: { jobUuid: job.job_uuid },
                        })
                      "
                      >{{ t("jobsList.edit") }}</Button
                    >
                    <Button
                      variant="destructive"
                      size="sm"
                      :disabled="deleteMutation.isPending.value"
                      @click="handleDelete(job.job_uuid)"
                    >
                      {{
                        deleteMutation.isPending.value
                          ? t("jobsList.deleting")
                          : t("jobsList.delete")
                      }}
                    </Button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  </section>
</template>

<style scoped>
.jobs-list-view {
  animation: rise-in 420ms ease-out both;
}

.jobs-list-card {
  border-color: hsl(var(--primary) / 0.2);
  background:
    radial-gradient(circle at 100% 0%, hsl(var(--accent) / 0.22), transparent 45%),
    linear-gradient(155deg, hsl(var(--card)) 0%, hsl(var(--background)) 100%);
  box-shadow: 0 12px 28px hsl(var(--primary) / 0.1);
}

@keyframes rise-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .jobs-list-view {
    animation: none;
  }
}
</style>
