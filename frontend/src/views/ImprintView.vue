<script setup lang="ts">
import { useI18n } from "vue-i18n";
import Button from "@/components/ui/button/Button.vue";

const { t } = useI18n();
</script>

<template>
  <section
    class="mx-auto my-8 max-w-3xl space-y-4 rounded-xl border bg-card p-6"
  >
    <p
      class="text-xs font-semibold uppercase tracking-wide text-muted-foreground"
    >
      {{ t("imprint.kicker") }}
    </p>
    <h1 class="text-2xl font-semibold">{{ t("imprint.title") }}</h1>
    <p class="text-sm text-muted-foreground">{{ t("imprint.subtitle") }}</p>

    <div
      class="space-y-3 rounded-md border bg-muted/25 p-4 text-sm text-muted-foreground"
    >
      <p class="font-semibold text-foreground">
        {{ t("imprint.section.provider") }}
      </p>
      <p>{{ t("imprint.person") }}</p>
      <p>{{ t("imprint.addressLine1") }}</p>
      <p>{{ t("imprint.addressLine2") }}</p>
      <p>{{ t("imprint.country") }}</p>
    </div>

    <div
      class="space-y-2 rounded-md border bg-muted/25 p-4 text-sm text-muted-foreground"
    >
      <p class="font-semibold text-foreground">
        {{ t("imprint.section.contact") }}
      </p>
      <p>
        {{ t("imprint.emailLabel") }}
        <a
          class="font-semibold text-foreground hover:underline"
          href="mailto:info@pegel-alarm.com"
          >info@pegel-alarm.com</a
        >
      </p>
    </div>

    <div
      class="space-y-2 rounded-md border bg-muted/25 p-4 text-sm text-muted-foreground"
    >
      <p class="font-semibold text-foreground">
        {{ t("imprint.section.disclaimer") }}
      </p>
      <p>{{ t("imprint.disclaimer.source") }}</p>
      <p>{{ t("imprint.disclaimer.informational") }}</p>
      <p>{{ t("imprint.disclaimer.noGuarantee") }}</p>
      <p>{{ t("imprint.disclaimer.liability") }}</p>
    </div>

    <Button variant="outline" @click="$router.push('/')">{{
      t("imprint.back")
    }}</Button>
  </section>
</template>
