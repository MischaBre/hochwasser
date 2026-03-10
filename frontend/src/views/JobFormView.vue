<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query";
import {
  Clock3,
  Gauge,
  Languages,
  MapPin,
  Send,
  Tag,
  Users,
} from "lucide-vue-next";
import { CronLight } from "@vue-js-cron/light";
import "@vue-js-cron/light/dist/light.css";
import Alert from "@/components/ui/alert/Alert.vue";
import Button from "@/components/ui/button/Button.vue";
import Card from "@/components/ui/card/Card.vue";
import CardContent from "@/components/ui/card/CardContent.vue";
import CardHeader from "@/components/ui/card/CardHeader.vue";
import CardTitle from "@/components/ui/card/CardTitle.vue";
import Input from "@/components/ui/input/Input.vue";
import Label from "@/components/ui/label/Label.vue";
import Textarea from "@/components/ui/textarea/Textarea.vue";
import { computed, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { ApiError, type ValidationIssue } from "@/api/client";
import { useFormatters } from "@/composables/useFormatters";
import { createJob, listJobs, updateJob } from "@/features/jobs/api";
import { listStations } from "@/features/stations/api";
import type { StationSummary } from "@/features/stations/types";
import {
  hasJobFormErrors,
  toCreatePayload,
  validateJobForm,
  type JobFormErrors,
  type JobFormField,
  type JobFormState,
} from "@/features/jobs/validation";

const route = useRoute();
const router = useRouter();
const queryClient = useQueryClient();
const { locale, t } = useI18n();
const { formatNumber } = useFormatters();

const jobUuid = computed(() => route.params.jobUuid as string | undefined);
const isEditMode = computed(() => route.name === "job-edit");

const form = reactive<JobFormState>({
  name: "",
  station_uuid: "",
  limit_cm: "0",
  recipients: "",
  alert_recipient: "",
  locale: "de",
  schedule_cron: "0 7,13,18 * * *",
  repeat_alerts_on_check: false,
  enabled: true,
});

const touched = reactive<Record<JobFormField, boolean>>({
  name: false,
  station_uuid: false,
  limit_cm: false,
  recipients: false,
  alert_recipient: false,
  locale: false,
  schedule_cron: false,
});

const submitAttempted = ref(false);
const serverErrors = reactive<JobFormErrors>({});
const clientErrors = computed(() => validateJobForm(form));
const stationSearch = ref("");
const stationPanelOpen = ref(false);
const cronEditorError = ref("");

const normalizeStationSearch = (value: string): string => {
  return value
    .toLocaleLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .trim()
    .replace(/\s+/g, " ");
};

const jobsQuery = useQuery({
  queryKey: ["jobs", "all"],
  queryFn: () => listJobs(true),
  enabled: isEditMode,
});

const currentJob = computed(() => {
  if (!jobUuid.value) {
    return null;
  }

  return (
    jobsQuery.data.value?.find((job) => job.job_uuid === jobUuid.value) ?? null
  );
});

const stationSearchTokens = computed(() => {
  const normalized = normalizeStationSearch(stationSearch.value);
  if (!normalized) {
    return [] as string[];
  }

  return normalized.split(" ").filter(Boolean);
});

const stationQueryTerm = computed(() => stationSearchTokens.value[0] ?? "");

const stationsQuery = useQuery({
  queryKey: computed(() => ["stations", "search", stationQueryTerm.value]),
  queryFn: () =>
    listStations({ search: stationQueryTerm.value, limit: 50, offset: 0 }),
  staleTime: 5 * 60 * 1000,
});

const selectedStationQuery = useQuery({
  queryKey: computed(() => ["stations", "selected", form.station_uuid]),
  queryFn: () =>
    listStations({ uuids: [form.station_uuid], limit: 1, offset: 0 }),
  enabled: computed(() => form.station_uuid.trim().length > 0),
  staleTime: 5 * 60 * 1000,
});

const stationSearchIndex = (station: StationSummary): string => {
  const water = station.water_longname || station.water_shortname;
  return normalizeStationSearch(
    [
      station.uuid,
      station.number,
      station.shortname,
      station.longname,
      station.agency,
      water,
    ]
      .filter(Boolean)
      .join(" "),
  );
};

const stationOptions = computed(() => {
  const items = stationsQuery.data.value?.items ?? [];
  if (stationSearchTokens.value.length === 0) {
    return items;
  }

  return items.filter((station) => {
    const index = stationSearchIndex(station);
    return stationSearchTokens.value.every((token) => index.includes(token));
  });
});
const selectedStation = computed(() => {
  if (selectedStationQuery.data.value?.items.length) {
    return selectedStationQuery.data.value.items[0];
  }

  return (
    stationOptions.value.find(
      (station) => station.uuid === form.station_uuid,
    ) ?? null
  );
});

const formatStationLabel = (station: StationSummary): string => {
  const water = station.water_longname || station.water_shortname;
  if (water) {
    return `${station.shortname} - ${water}`;
  }

  return station.shortname;
};

const formatStationDetails = (station: StationSummary): string => {
  const water = station.water_longname || station.water_shortname || "-";
  const km =
    station.km === null
      ? "-"
      : formatNumber(station.km, { maximumFractionDigits: 2 });
  const coordinates =
    station.latitude === null || station.longitude === null
      ? "-"
      : `${formatNumber(station.latitude, { maximumFractionDigits: 5 })}, ${formatNumber(station.longitude, { maximumFractionDigits: 5 })}`;

  return [
    t("jobForm.station.detailUuid", { value: station.uuid }),
    t("jobForm.station.detailLongName", { value: station.longname }),
    t("jobForm.station.detailWater", { value: water }),
    t("jobForm.station.detailAgency", { value: station.agency || "-" }),
    t("jobForm.station.detailNumber", { value: station.number || "-" }),
    t("jobForm.station.detailKm", { value: km }),
    t("jobForm.station.detailCoords", { value: coordinates }),
  ].join(" | ");
};

const stationHint = computed(() => {
  if (!selectedStation.value) {
    return "";
  }

  const station = selectedStation.value;
  const pieces = [station.longname];
  if (station.agency) {
    pieces.push(station.agency);
  }
  pieces.push(station.uuid);
  return pieces.join(" | ");
});

const stationQueryError = computed(() => {
  const error = stationsQuery.error.value;
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "";
});

const onStationSearchChange = (value: string): void => {
  stationSearch.value = value;
  stationPanelOpen.value = true;

  if (
    selectedStation.value &&
    normalizeStationSearch(value) ===
      normalizeStationSearch(formatStationLabel(selectedStation.value))
  ) {
    return;
  }

  form.station_uuid = "";
  clearServerError("station_uuid");
};

const selectStation = (station: StationSummary): void => {
  form.station_uuid = station.uuid;
  stationSearch.value = formatStationLabel(station);
  stationPanelOpen.value = false;
  markTouched("station_uuid");
  clearServerError("station_uuid");
};

const onStationSearchFocus = (): void => {
  stationPanelOpen.value = true;
};

const onStationSearchBlur = (): void => {
  stationPanelOpen.value = false;
  markTouched("station_uuid");
};

const onLimitChange = (value: string): void => {
  form.limit_cm = value.replace(/\D+/g, "");
  clearServerError("limit_cm");
};

const onScheduleCronChange = (value: string): void => {
  form.schedule_cron = value;
  cronEditorError.value = "";
  markTouched("schedule_cron");
  clearServerError("schedule_cron");
};

const onScheduleCronError = (value: string): void => {
  cronEditorError.value = value;
};

const cronLocale = computed(() => (locale.value === "de" ? "de" : "en"));

const showNoStationMatches = computed(() => {
  if (stationsQuery.isLoading.value) {
    return false;
  }

  if (stationOptions.value.length > 0) {
    return false;
  }

  if (!stationSearch.value.trim()) {
    return false;
  }

  if (
    selectedStation.value &&
    normalizeStationSearch(stationSearch.value) ===
      normalizeStationSearch(formatStationLabel(selectedStation.value))
  ) {
    return false;
  }

  return true;
});

const showStationResultsPanel = computed(() => {
  if (!stationPanelOpen.value) {
    return false;
  }

  return (
    stationsQuery.isLoading.value ||
    stationOptions.value.length > 0 ||
    showNoStationMatches.value
  );
});

const clearServerError = (field: JobFormField | "form"): void => {
  delete serverErrors[field];
};

const markTouched = (field: JobFormField): void => {
  touched[field] = true;
};

const getFieldError = (field: JobFormField): string => {
  if (serverErrors[field]) {
    return serverErrors[field] as string;
  }

  if (submitAttempted.value || touched[field]) {
    return clientErrors.value[field] ?? "";
  }

  return "";
};

const mapValidationIssues = (issues: ValidationIssue[]): JobFormErrors => {
  const nextErrors: JobFormErrors = {};

  for (const issue of issues) {
    const message = issue.msg?.trim();
    if (!message) {
      continue;
    }

    const loc =
      issue.loc?.filter(
        (value): value is string => typeof value === "string",
      ) ?? [];
    let field: JobFormField | undefined;

    for (let index = loc.length - 1; index >= 0; index -= 1) {
      const value = loc[index];
      if (
        value === "name" ||
        value === "station_uuid" ||
        value === "limit_cm" ||
        value === "recipients" ||
        value === "alert_recipient" ||
        value === "locale" ||
        value === "schedule_cron"
      ) {
        field = value;
        break;
      }
    }

    if (field && !nextErrors[field]) {
      nextErrors[field] = message;
      continue;
    }

    if (!nextErrors.form) {
      nextErrors.form = message;
    }
  }

  return nextErrors;
};

watch(
  currentJob,
  (job) => {
    if (!job) {
      return;
    }

    form.name = job.name;
    form.station_uuid = job.station_uuid;
    stationSearch.value = job.station_uuid;
    form.limit_cm = String(job.limit_cm);
    form.recipients = job.recipients.join(", ");
    form.alert_recipient = job.alert_recipient;
    form.locale = job.locale;
    form.schedule_cron = job.schedule_cron;
    form.repeat_alerts_on_check = job.repeat_alerts_on_check;
    form.enabled = job.enabled;

    for (const field of Object.keys(touched) as JobFormField[]) {
      touched[field] = false;
    }

    submitAttempted.value = false;
    for (const key of Object.keys(serverErrors) as Array<
      JobFormField | "form"
    >) {
      delete serverErrors[key];
    }
  },
  { immediate: true },
);

watch(selectedStation, (station) => {
  if (!station) {
    return;
  }

  if (!stationSearch.value || stationSearch.value === form.station_uuid) {
    stationSearch.value = formatStationLabel(station);
  }
});

const submitMutation = useMutation({
  mutationFn: async () => {
    const payload = toCreatePayload(form);

    if (isEditMode.value && jobUuid.value) {
      return updateJob(jobUuid.value, { ...payload, enabled: form.enabled });
    }

    return createJob(payload);
  },
  onSuccess: async (job) => {
    await queryClient.invalidateQueries({ queryKey: ["jobs"] });
    await router.push({
      name: "job-details",
      params: { jobUuid: job.job_uuid },
    });
  },
  onError: (error) => {
    if (error instanceof ApiError && error.validationIssues.length > 0) {
      const mappedErrors = mapValidationIssues(error.validationIssues);
      for (const key of Object.keys(serverErrors) as Array<
        JobFormField | "form"
      >) {
        delete serverErrors[key];
      }
      for (const [key, value] of Object.entries(mappedErrors) as Array<
        [JobFormField | "form", string]
      >) {
        serverErrors[key] = value;
      }
    }
  },
});

const submitError = computed(() => {
  const error = submitMutation.error.value;
  if (error instanceof ApiError) {
    if (error.validationIssues.length > 0) {
      return "";
    }
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "";
});

const submit = async () => {
  submitAttempted.value = true;
  clearServerError("form");

  if (hasJobFormErrors(clientErrors.value)) {
    return;
  }

  await submitMutation.mutateAsync();
};
</script>

<template>
  <section>
    <Card>
      <CardHeader>
        <CardTitle>{{
          isEditMode ? t("jobForm.editTitle") : t("jobForm.createTitle")
        }}</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="space-y-4">
          <Alert v-if="isEditMode && jobsQuery.isLoading.value">{{
            t("jobForm.loadingJob")
          }}</Alert>
          <Alert
            v-if="isEditMode && !jobsQuery.isLoading.value && !currentJob"
            variant="destructive"
            >{{ t("jobForm.jobNotFound") }}</Alert
          >
          <Alert v-if="serverErrors.form" variant="destructive">{{
            serverErrors.form
          }}</Alert>
          <Alert
            v-if="submitMutation.isError.value && submitError"
            variant="destructive"
            >{{ submitError }}</Alert
          >

          <form
            class="grid gap-x-4 gap-y-6 md:grid-cols-2"
            @submit.prevent="submit"
          >
            <div class="space-y-2">
              <Label for="job-name">{{ t("jobForm.fields.name") }}</Label>
              <div class="relative">
                <Tag
                  class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
                />
                <Input
                  id="job-name"
                  v-model="form.name"
                  class="pl-9"
                  required
                  @blur="markTouched('name')"
                  @input="clearServerError('name')"
                />
              </div>
              <p v-if="getFieldError('name')" class="text-sm text-destructive">
                {{ getFieldError("name") }}
              </p>
            </div>

            <div class="space-y-2">
              <Label for="station-search">{{
                t("jobForm.fields.station")
              }}</Label>
              <div class="relative">
                <MapPin
                  class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
                />
                <Input
                  id="station-search"
                  :model-value="stationSearch"
                  class="pl-9"
                  :placeholder="t('jobForm.fields.stationPlaceholder')"
                  required
                  @focus="onStationSearchFocus"
                  @blur="onStationSearchBlur"
                  @update:model-value="onStationSearchChange"
                />
              </div>

              <div
                v-if="showStationResultsPanel"
                class="max-h-44 overflow-y-auto rounded-md border"
              >
                <button
                  v-for="station in stationOptions"
                  :key="station.uuid"
                  type="button"
                  class="flex w-full flex-col items-start gap-0.5 border-b px-3 py-2 text-left last:border-b-0 hover:bg-accent"
                  @mousedown.prevent
                  @click="selectStation(station)"
                >
                  <span class="text-sm font-medium">{{
                    formatStationLabel(station)
                  }}</span>
                  <span class="text-xs text-muted-foreground">{{
                    formatStationDetails(station)
                  }}</span>
                </button>
                <div
                  v-if="stationsQuery.isLoading.value"
                  class="px-3 py-2 text-xs text-muted-foreground"
                >
                  {{ t("jobForm.station.loading") }}
                </div>
                <div
                  v-else-if="showNoStationMatches"
                  class="px-3 py-2 text-xs text-muted-foreground"
                >
                  {{ t("jobForm.station.noMatch") }}
                </div>
              </div>

              <p v-if="stationHint" class="text-xs text-muted-foreground">
                {{ t("jobForm.station.selected", { value: stationHint }) }}
              </p>
              <p v-if="stationQueryError" class="text-xs text-destructive">
                {{ stationQueryError }}
              </p>
              <p
                v-if="getFieldError('station_uuid')"
                class="text-sm text-destructive"
              >
                {{ getFieldError("station_uuid") }}
              </p>
            </div>

            <div class="space-y-2">
              <Label for="limit-cm">{{ t("jobForm.fields.limitCm") }}</Label>
              <div class="relative">
                <Gauge
                  class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
                />
                <Input
                  id="limit-cm"
                  :model-value="form.limit_cm"
                  class="pl-9"
                  type="number"
                  min="0"
                  step="1"
                  inputmode="numeric"
                  required
                  @blur="markTouched('limit_cm')"
                  @update:model-value="onLimitChange"
                />
              </div>
              <p
                v-if="getFieldError('limit_cm')"
                class="text-sm text-destructive"
              >
                {{ getFieldError("limit_cm") }}
              </p>
            </div>

            <div class="space-y-2">
              <Label for="locale">{{ t("jobForm.fields.locale") }}</Label>
              <div class="relative">
                <Languages
                  class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
                />
                <select
                  id="locale"
                  v-model="form.locale"
                  class="flex h-10 w-full rounded-md border border-input bg-background pl-9 pr-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  @blur="markTouched('locale')"
                  @change="clearServerError('locale')"
                >
                  <option value="de">
                    {{ t("jobForm.fields.localeGerman") }}
                  </option>
                  <option value="en">
                    {{ t("jobForm.fields.localeEnglish") }}
                  </option>
                </select>
              </div>
              <p
                v-if="getFieldError('locale')"
                class="text-sm text-destructive"
              >
                {{ getFieldError("locale") }}
              </p>
            </div>

            <div class="space-y-2 md:col-span-2">
              <Label for="recipients">{{
                t("jobForm.fields.recipients")
              }}</Label>
              <div class="relative">
                <Users
                  class="pointer-events-none absolute left-3 top-3 h-4 w-4 text-muted-foreground"
                />
                <Textarea
                  id="recipients"
                  v-model="form.recipients"
                  rows="3"
                  class="pl-9"
                  :placeholder="t('jobForm.fields.recipientsPlaceholder')"
                  required
                  @blur="markTouched('recipients')"
                  @input="clearServerError('recipients')"
                />
              </div>
              <p class="text-xs text-muted-foreground">
                {{ t("jobForm.fields.recipientsHint") }}
              </p>
              <p
                v-if="getFieldError('recipients')"
                class="text-sm text-destructive"
              >
                {{ getFieldError("recipients") }}
              </p>
            </div>

            <div class="space-y-2 md:col-span-2">
              <Label for="schedule-cron">{{
                t("jobForm.fields.scheduleCron")
              }}</Label>
              <div class="space-y-4 rounded-md border p-4">
                <CronLight
                  :key="`cron-${cronLocale}`"
                  :model-value="form.schedule_cron"
                  format="crontab"
                  :locale="cronLocale"
                  @update:model-value="onScheduleCronChange"
                  @error="onScheduleCronError"
                />

                <div class="space-y-2">
                  <div class="relative">
                    <Clock3
                      class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
                    />
                    <Input
                      id="schedule-cron"
                      :model-value="form.schedule_cron"
                      class="pl-9"
                      :placeholder="t('jobForm.fields.scheduleCronPlaceholder')"
                      required
                      @blur="markTouched('schedule_cron')"
                      @update:model-value="onScheduleCronChange"
                    />
                  </div>

                  <p class="text-xs text-muted-foreground">
                    {{ t("jobForm.fields.scheduleCronHint") }}
                  </p>
                </div>

                <p v-if="cronEditorError" class="text-xs text-muted-foreground">
                  {{
                    t("jobForm.fields.scheduleCronEditorError", {
                      message: cronEditorError,
                    })
                  }}
                </p>
              </div>
              <p class="text-xs text-muted-foreground">
                {{ t("jobForm.fields.scheduleCronCheckInfo") }}
              </p>
              <p
                v-if="getFieldError('schedule_cron')"
                class="text-sm text-destructive"
              >
                {{ getFieldError("schedule_cron") }}
              </p>
            </div>

            <div class="space-y-2 md:col-span-2">
              <Label for="alert-recipient">{{
                t("jobForm.fields.alertRecipient")
              }}</Label>
              <div class="relative">
                <Send
                  class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
                />
                <Input
                  id="alert-recipient"
                  v-model="form.alert_recipient"
                  class="pl-9"
                  type="email"
                  :placeholder="t('jobForm.fields.alertRecipientPlaceholder')"
                  required
                  @blur="markTouched('alert_recipient')"
                  @input="clearServerError('alert_recipient')"
                />
              </div>
              <p class="text-xs text-muted-foreground">
                {{ t("jobForm.fields.alertRecipientHint") }}
              </p>
              <p
                v-if="getFieldError('alert_recipient')"
                class="text-sm text-destructive"
              >
                {{ getFieldError("alert_recipient") }}
              </p>
            </div>

            <div
              class="md:col-span-2 flex flex-wrap items-start gap-4 text-sm text-muted-foreground"
            >
              <div class="space-y-2">
                <div class="flex items-center gap-2">
                  <input
                    id="repeat-alerts"
                    v-model="form.repeat_alerts_on_check"
                    type="checkbox"
                    class="h-4 w-4 rounded border-input"
                  />
                  <Label for="repeat-alerts">{{
                    t("jobForm.fields.repeatAlertsOnCheck")
                  }}</Label>
                </div>
                <span
                  class="inline-block cursor-help text-xs font-medium text-muted-foreground underline decoration-dotted underline-offset-2"
                  :title="t('jobForm.fields.repeatAlertsOnCheckHint')"
                  :aria-label="t('jobForm.fields.repeatAlertsOnCheckHint')"
                >
                  {{ t("jobForm.fields.moreInfo") }}
                </span>
              </div>
              <div v-if="isEditMode" class="flex items-center gap-2">
                <input
                  id="job-enabled"
                  v-model="form.enabled"
                  type="checkbox"
                  class="h-4 w-4 rounded border-input"
                />
                <Label for="job-enabled">{{
                  t("jobForm.fields.enabled")
                }}</Label>
              </div>
            </div>

            <div class="md:col-span-2 flex items-center justify-end gap-2 pt-2">
              <Button
                variant="outline"
                @click="router.push({ name: 'jobs' })"
                >{{ t("jobForm.actions.cancel") }}</Button
              >
              <Button
                type="submit"
                :disabled="
                  submitMutation.isPending.value ||
                  hasJobFormErrors(clientErrors) ||
                  (isEditMode && !currentJob)
                "
              >
                {{
                  submitMutation.isPending.value
                    ? t("jobForm.actions.saving")
                    : isEditMode
                      ? t("jobForm.actions.saveChanges")
                      : t("jobForm.actions.saveCreate")
                }}
              </Button>
            </div>
          </form>
        </div>
      </CardContent>
    </Card>
  </section>
</template>
