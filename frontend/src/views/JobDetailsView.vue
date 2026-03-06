<script setup lang="ts">
import { useQuery } from "@tanstack/vue-query";
import Alert from "@/components/ui/alert/Alert.vue";
import Badge from "@/components/ui/badge/Badge.vue";
import Button from "@/components/ui/button/Button.vue";
import Card from "@/components/ui/card/Card.vue";
import CardContent from "@/components/ui/card/CardContent.vue";
import CardHeader from "@/components/ui/card/CardHeader.vue";
import CardTitle from "@/components/ui/card/CardTitle.vue";
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { ApiError } from "@/api/client";
import { useFormatters } from "@/composables/useFormatters";
import { getJobOutbox, getJobStatus, listJobs } from "@/features/jobs/api";
import { listStations } from "@/features/stations/api";

const route = useRoute();
const router = useRouter();
const { t, te } = useI18n();
const { formatDateTime, formatRelativeDateTime, formatNumber } =
  useFormatters();
const jobUuid = computed(() => route.params.jobUuid as string);

const outboxLimit = ref(20);
const outboxOffset = ref(0);

const jobsQuery = useQuery({
  queryKey: ["jobs", "all"],
  queryFn: () => listJobs(true),
});

const job = computed(() =>
  jobsQuery.data.value?.find((item) => item.job_uuid === jobUuid.value),
);

const stationQuery = useQuery({
  queryKey: computed(() => [
    "stations",
    "job-details",
    job.value?.station_uuid || "",
  ]),
  queryFn: () =>
    listStations({
      uuids: [job.value?.station_uuid || ""],
      limit: 1,
      offset: 0,
    }),
  enabled: computed(() => Boolean(job.value?.station_uuid)),
  staleTime: 5 * 60 * 1000,
});

const station = computed(() => stationQuery.data.value?.items[0] ?? null);

const statusQuery = useQuery({
  queryKey: computed(() => ["job-status", jobUuid.value]),
  queryFn: () => getJobStatus(jobUuid.value),
});

const outboxQuery = useQuery({
  queryKey: computed(() => [
    "job-outbox",
    jobUuid.value,
    outboxLimit.value,
    outboxOffset.value,
  ]),
  queryFn: () =>
    getJobOutbox(jobUuid.value, outboxLimit.value, outboxOffset.value),
});

const statusError = computed(() => {
  const error = statusQuery.error.value;
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "";
});

const outboxError = computed(() => {
  const error = outboxQuery.error.value;
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "";
});

const nextPage = () => {
  if ((outboxQuery.data.value?.items.length ?? 0) < outboxLimit.value) {
    return;
  }

  outboxOffset.value += outboxLimit.value;
};

const prevPage = () => {
  outboxOffset.value = Math.max(0, outboxOffset.value - outboxLimit.value);
};

const formatOptionalDateTimeWithRelative = (value: string | null): string => {
  if (!value) {
    return t("jobDetails.fields.na");
  }

  const absolute = formatDateTime(value);
  const relative = formatRelativeDateTime(value);

  return relative ? `${absolute} (${relative})` : absolute;
};

const toTranslationToken = (value: string): string => {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
};

const translateStatusState = (value: string | null): string => {
  if (!value) {
    return t("jobDetails.fields.na");
  }

  const token = toTranslationToken(value);
  const key = `jobDetails.status.stateValues.${token}`;
  return te(key) ? t(key) : value;
};

const translateOutboxReason = (value: string): string => {
  const token = toTranslationToken(value);
  const key = `jobDetails.outbox.reasonValues.${token}`;
  return token && te(key) ? t(key) : value;
};

const translateOutboxTarget = (value: string): string => {
  const token = toTranslationToken(value);
  const key = `jobDetails.outbox.targetValues.${token}`;
  return token && te(key) ? t(key) : value;
};

const translateOutboxStatus = (value: string): string => {
  const token = toTranslationToken(value);
  const key = `jobDetails.outbox.statusValues.${token}`;
  return token && te(key) ? t(key) : value;
};
</script>

<template>
  <section class="space-y-4">
    <Card>
      <CardHeader>
        <div
          class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between"
        >
          <CardTitle>{{
            job?.name || t("jobDetails.titleFallback")
          }}</CardTitle>
          <div class="flex gap-2">
            <Button variant="outline" @click="router.push({ name: 'jobs' })">{{
              t("jobDetails.back")
            }}</Button>
            <Button
              variant="outline"
              :disabled="!job"
              @click="router.push({ name: 'job-edit', params: { jobUuid } })"
            >
              {{ t("jobDetails.edit") }}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div
          v-if="jobsQuery.isLoading.value"
          class="text-sm text-muted-foreground"
        >
          {{ t("jobDetails.loadingJob") }}
        </div>
        <Alert v-else-if="!job" variant="destructive">{{
          t("jobDetails.jobNotFound")
        }}</Alert>
        <div
          v-else
          class="grid gap-4 text-sm text-muted-foreground md:grid-cols-2"
        >
          <div class="space-y-2 rounded-md border bg-muted/30 p-4">
            <p>
              <span class="font-semibold text-foreground"
                >{{ t("jobDetails.fields.station") }}:</span
              >
              {{
                station
                  ? `${station.shortname} - ${station.longname}`
                  : job.station_uuid
              }}
            </p>
            <p>
              <span class="font-semibold text-foreground"
                >{{ t("jobDetails.fields.water") }}:</span
              >
              {{
                station?.water_longname ||
                station?.water_shortname ||
                t("jobDetails.fields.na")
              }}
            </p>
            <p>
              <span class="font-semibold text-foreground"
                >{{ t("jobDetails.fields.agency") }}:</span
              >
              {{ station?.agency || t("jobDetails.fields.na") }}
            </p>
            <p>
              <span class="font-semibold text-foreground"
                >{{ t("jobDetails.fields.coordinates") }}:</span
              >
              {{
                station?.latitude !== null && station?.latitude !== undefined
                  ? formatNumber(station.latitude, { maximumFractionDigits: 5 })
                  : t("jobDetails.fields.na")
              }},
              {{
                station?.longitude !== null && station?.longitude !== undefined
                  ? formatNumber(station.longitude, {
                      maximumFractionDigits: 5,
                    })
                  : t("jobDetails.fields.na")
              }}
            </p>
            <p>
              <span class="font-semibold text-foreground"
                >{{ t("jobDetails.fields.stationUuid") }}:</span
              >
              {{ job.station_uuid }}
            </p>
            <p>
              <span class="font-semibold text-foreground"
                >{{ t("jobDetails.fields.limit") }}:</span
              >
              {{ formatNumber(job.limit_cm) }} cm
            </p>
            <p>
              <span class="font-semibold text-foreground"
                >{{ t("jobDetails.fields.schedule") }}:</span
              >
              {{ job.schedule_cron }}
            </p>
            <p>
              <span class="font-semibold text-foreground"
                >{{ t("jobDetails.fields.locale") }}:</span
              >
              {{ job.locale }}
            </p>
            <p>
              <span class="font-semibold text-foreground"
                >{{ t("jobDetails.fields.alertRecipient") }}:</span
              >
              {{ job.alert_recipient }}
            </p>
            <p>
              <span class="font-semibold text-foreground"
                >{{ t("jobDetails.fields.recipients") }}:</span
              >
              {{ job.recipients.join(", ") }}
            </p>
            <Badge :variant="job.enabled ? 'default' : 'secondary'">{{
              job.enabled ? t("jobDetails.enabled") : t("jobDetails.disabled")
            }}</Badge>
          </div>

          <div class="space-y-2 rounded-md border bg-muted/30 p-4">
            <p class="font-semibold text-foreground">
              {{ t("jobDetails.fields.statusTitle") }}
            </p>
            <Alert
              v-if="statusQuery.isError.value && statusError"
              variant="destructive"
              >{{ statusError }}</Alert
            >
            <div
              v-else-if="statusQuery.isLoading.value"
              class="text-sm text-muted-foreground"
            >
              {{ t("jobDetails.status.loading") }}
            </div>
            <div v-else-if="statusQuery.data.value" class="space-y-2">
              <p>
                <span class="font-semibold text-foreground"
                  >{{ t("jobDetails.fields.state") }}:</span
                >
                {{ translateStatusState(statusQuery.data.value.state) }}
              </p>
              <p>
                <span class="font-semibold text-foreground"
                  >{{ t("jobDetails.fields.stateSince") }}:</span
                >
                {{
                  formatOptionalDateTimeWithRelative(
                    statusQuery.data.value.state_since,
                  )
                }}
              </p>
              <p>
                <span class="font-semibold text-foreground"
                  >{{ t("jobDetails.fields.predictedPeak") }}:</span
                >
                {{
                  statusQuery.data.value.predicted_peak_cm !== null
                    ? formatNumber(statusQuery.data.value.predicted_peak_cm)
                    : t("jobDetails.fields.na")
                }}
                {{ t("jobDetails.fields.at") }}
                {{
                  formatOptionalDateTimeWithRelative(
                    statusQuery.data.value.predicted_peak_at,
                  )
                }}
              </p>
              <p>
                <span class="font-semibold text-foreground"
                  >{{ t("jobDetails.fields.lastNotified") }}:</span
                >
                {{
                  formatOptionalDateTimeWithRelative(
                    statusQuery.data.value.last_notified_at,
                  )
                }}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <div class="flex items-center justify-between">
          <CardTitle>{{ t("jobDetails.outbox.title") }}</CardTitle>
          <p class="text-xs text-muted-foreground">
            {{
              t("jobDetails.outbox.limitOffset", {
                limit: formatNumber(outboxLimit),
                offset: formatNumber(outboxOffset),
              })
            }}
          </p>
        </div>
      </CardHeader>
      <CardContent>
        <Alert
          v-if="outboxQuery.isError.value && outboxError"
          variant="destructive"
          >{{ outboxError }}</Alert
        >
        <div
          v-else-if="outboxQuery.isLoading.value"
          class="text-sm text-muted-foreground"
        >
          {{ t("jobDetails.outbox.loading") }}
        </div>
        <div
          v-else-if="
            !outboxQuery.data.value || outboxQuery.data.value.items.length === 0
          "
          class="text-sm text-muted-foreground"
        >
          {{ t("jobDetails.outbox.empty") }}
        </div>
        <div v-else class="space-y-4">
          <div class="overflow-x-auto">
            <table
              class="w-full min-w-[820px] border-collapse text-left text-sm"
            >
              <thead>
                <tr
                  class="border-b text-xs uppercase tracking-wide text-muted-foreground"
                >
                  <th class="py-3 pr-4">
                    {{ t("jobDetails.outbox.table.id") }}
                  </th>
                  <th class="py-3 pr-4">
                    {{ t("jobDetails.outbox.table.target") }}
                  </th>
                  <th class="py-3 pr-4">
                    {{ t("jobDetails.outbox.table.reason") }}
                  </th>
                  <th class="py-3 pr-4">
                    {{ t("jobDetails.outbox.table.status") }}
                  </th>
                  <th class="py-3 pr-4">
                    {{ t("jobDetails.outbox.table.attempts") }}
                  </th>
                  <th class="py-3">
                    {{ t("jobDetails.outbox.table.nextAttempt") }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="entry in outboxQuery.data.value.items"
                  :key="entry.id"
                  class="border-b last:border-none"
                >
                  <td class="py-3 pr-4">{{ formatNumber(entry.id) }}</td>
                  <td class="py-3 pr-4">
                    {{ translateOutboxTarget(entry.target_state) }}
                  </td>
                  <td class="py-3 pr-4">
                    {{ translateOutboxReason(entry.trigger_reason) }}
                  </td>
                  <td class="py-3 pr-4">
                    {{ translateOutboxStatus(entry.status) }}
                  </td>
                  <td class="py-3 pr-4">
                    {{ formatNumber(entry.attempt_count) }}
                  </td>
                  <td class="py-3">
                    {{
                      formatOptionalDateTimeWithRelative(entry.next_attempt_at)
                    }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="flex justify-end gap-2">
            <Button
              variant="outline"
              size="sm"
              :disabled="outboxOffset === 0"
              @click="prevPage"
              >{{ t("jobDetails.outbox.previous") }}</Button
            >
            <Button
              variant="outline"
              size="sm"
              :disabled="
                (outboxQuery.data.value?.items.length ?? 0) < outboxLimit
              "
              @click="nextPage"
            >
              {{ t("jobDetails.outbox.next") }}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  </section>
</template>
