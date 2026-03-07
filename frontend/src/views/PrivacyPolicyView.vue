<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import Button from "@/components/ui/button/Button.vue";

const { t } = useI18n();

const rights = computed(() => {
  return [
    t("privacy.rights.items.access"),
    t("privacy.rights.items.rectification"),
    t("privacy.rights.items.erasure"),
    t("privacy.rights.items.restriction"),
    t("privacy.rights.items.portability"),
    t("privacy.rights.items.object"),
  ];
});

const logfileItems = computed(() => {
  return [
    t("privacy.logfiles.items.ip"),
    t("privacy.logfiles.items.time"),
    t("privacy.logfiles.items.resource"),
    t("privacy.logfiles.items.status"),
    t("privacy.logfiles.items.browser"),
    t("privacy.logfiles.items.os"),
    t("privacy.logfiles.items.referrer"),
  ];
});

const cookieItems = computed(() => {
  return [t("privacy.cookies.items.login"), t("privacy.cookies.items.session")];
});
</script>

<template>
  <section
    class="mx-auto my-8 max-w-3xl space-y-4 rounded-xl border bg-card p-6"
  >
    <h1 class="text-2xl font-semibold">{{ t("privacy.title") }}</h1>

    <div
      class="space-y-2 rounded-md border bg-muted/25 p-4 text-sm text-muted-foreground"
    >
      <h2 class="font-semibold text-foreground">
        {{ t("privacy.controller.title") }}
      </h2>
      <p>{{ t("privacy.controller.person") }}</p>
      <p>{{ t("privacy.controller.addressLine1") }}</p>
      <p>{{ t("privacy.controller.addressLine2") }}</p>
      <p>{{ t("privacy.controller.country") }}</p>
      <p>
        {{ t("privacy.controller.emailLabel") }}
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
      <h2 class="font-semibold text-foreground">
        {{ t("privacy.logfiles.title") }}
      </h2>
      <p>{{ t("privacy.logfiles.description") }}</p>
      <ul class="list-disc pl-5">
        <li v-for="entry in logfileItems" :key="entry">{{ entry }}</li>
      </ul>
      <p>{{ t("privacy.logfiles.purpose") }}</p>
      <p>{{ t("privacy.logfiles.legalBasis") }}</p>
    </div>

    <div
      class="space-y-2 rounded-md border bg-muted/25 p-4 text-sm text-muted-foreground"
    >
      <h2 class="font-semibold text-foreground">
        {{ t("privacy.cookies.title") }}
      </h2>
      <p>{{ t("privacy.cookies.description") }}</p>
      <ul class="list-disc pl-5">
        <li v-for="entry in cookieItems" :key="entry">{{ entry }}</li>
      </ul>
      <p>{{ t("privacy.cookies.noTracking") }}</p>
      <p>{{ t("privacy.cookies.legalBasis") }}</p>
      <p>{{ t("privacy.cookies.noBanner") }}</p>
    </div>

    <div
      class="space-y-2 rounded-md border bg-muted/25 p-4 text-sm text-muted-foreground"
    >
      <h2 class="font-semibold text-foreground">
        {{ t("privacy.email.title") }}
      </h2>
      <p>{{ t("privacy.email.description") }}</p>
      <p>{{ t("privacy.email.legalBasis") }}</p>
    </div>

    <div
      class="space-y-2 rounded-md border bg-muted/25 p-4 text-sm text-muted-foreground"
    >
      <h2 class="font-semibold text-foreground">
        {{ t("privacy.sharing.title") }}
      </h2>
      <p>{{ t("privacy.sharing.description") }}</p>
    </div>

    <div
      class="space-y-2 rounded-md border bg-muted/25 p-4 text-sm text-muted-foreground"
    >
      <h2 class="font-semibold text-foreground">
        {{ t("privacy.retention.title") }}
      </h2>
      <p>{{ t("privacy.retention.description") }}</p>
      <p>{{ t("privacy.retention.logfiles") }}</p>
    </div>

    <div
      class="space-y-2 rounded-md border bg-muted/25 p-4 text-sm text-muted-foreground"
    >
      <h2 class="font-semibold text-foreground">
        {{ t("privacy.rights.title") }}
      </h2>
      <ul class="list-disc pl-5">
        <li v-for="entry in rights" :key="entry">{{ entry }}</li>
      </ul>
      <p>{{ t("privacy.rights.contact") }}</p>
    </div>

    <div
      class="space-y-2 rounded-md border bg-muted/25 p-4 text-sm text-muted-foreground"
    >
      <h2 class="font-semibold text-foreground">
        {{ t("privacy.supervisory.title") }}
      </h2>
      <p>{{ t("privacy.supervisory.description") }}</p>
      <p>{{ t("privacy.supervisory.authority") }}</p>
      <a
        class="font-semibold text-foreground hover:underline"
        href="https://www.ldi.nrw.de"
        target="_blank"
        rel="noreferrer"
        >https://www.ldi.nrw.de</a
      >
    </div>

    <Button variant="outline" @click="$router.push('/')">{{
      t("privacy.back")
    }}</Button>
  </section>
</template>
