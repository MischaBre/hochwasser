const en = {
  shell: {
    appName: "Hochwasser",
    appSection: "Operations Deck",
    nav: {
      overview: "Dashboard",
      jobs: "Jobs",
    },
    actions: {
      signOut: "Sign out",
    },
    locale: {
      label: "Language",
      de: "DE",
      en: "EN",
    },
    footer: {
      source:
        "Data source and station metadata are provided by official public sources.",
      imprint: "Imprint",
      privacy: "Privacy policy",
    },
  },
  auth: {
    login: {
      title: "Welcome back",
      email: "Email",
      password: "Password",
      hidePassword: "Hide password",
      showPassword: "Show password",
      submit: "Sign in",
      submitting: "Signing in...",
      newHere: "New here?",
      createAccount: "Create account",
      cancel: "Cancel",
      close: "Close login dialog",
      failedFallback: "Login failed. Please try again.",
    },
    register: {
      title: "Create your account",
      email: "Email",
      password: "Password",
      confirmPassword: "Confirm password",
      hidePassword: "Hide password",
      showPassword: "Show password",
      hideConfirmPassword: "Hide confirm password",
      showConfirmPassword: "Show confirm password",
      submit: "Create account",
      submitting: "Creating account...",
      backToLogin: "Back to login",
      passwordsMismatch: "Passwords do not match.",
      createdCheckInbox:
        "Account created. Check your inbox to confirm your email, then sign in.",
      failedFallback: "Registration failed. Please try again.",
    },
  },
  landing: {
    kicker: "Flood early warning workspace",
    title: "Monitor your stations and react before levels become critical.",
    copy: "Hochwasser Alarm combines official station data, threshold-based alerting, and practical job controls in one focused dashboard.",
    actions: {
      signIn: "Sign in",
      createAccount: "Create account",
      openDashboard: "Open dashboard",
      startNow: "Start now",
      imprint: "Imprint",
      privacy: "Privacy policy",
    },
    features: {
      alerting: {
        title: "Threshold alerts that stay actionable",
        copy: "Configure one job per station, set clear limits, and keep alert noise under control.",
      },
      monitoring: {
        title: "Live-oriented operational overview",
        copy: "See job status, recent trends, and relevant context at a glance for faster decisions.",
      },
      sources: {
        title: "Official source integration",
        copy: "Station and water-level information is sourced from official public provider interfaces.",
      },
    },
    footer: {
      source:
        "Informational support only. Always follow official warnings and emergency guidance.",
    },
  },
  imprint: {
    kicker: "Legal notice",
    title: "Imprint",
    subtitle:
      "Information according to Section 5 German Digital Services Act (DDG)",
    section: {
      provider: "Provider",
      contact: "Contact",
      disclaimer: "Liability and service disclaimer",
    },
    person: "Michael Breyer",
    addressLine1: "Siebengbirgsallee 51",
    addressLine2: "50939 Cologne",
    country: "Germany",
    emailLabel: "Email:",
    disclaimer: {
      source:
        "Water-level and station data come from official public provider interfaces. This project does not claim ownership of these data.",
      informational:
        "This service is informational support only and does not replace official warnings, emergency alerts, or civil protection guidance.",
      noGuarantee:
        "No guarantee is given for availability, correctness, completeness, timeliness, or alert delivery.",
      liability:
        "The operator is not liable for damages caused by delayed, missing, or incorrect alerts.",
    },
    back: "Back to home",
  },
  privacy: {
    title: "Privacy policy",
    controller: {
      title: "1. Controller",
      person: "Michael Breyer",
      addressLine1: "Siebengbirgsallee 51",
      addressLine2: "50939 Cologne",
      country: "Germany",
      emailLabel: "Email:",
    },
    logfiles: {
      title: "2. Server log files",
      description:
        "When this website is accessed, information is automatically collected by the web server and stored in server log files.",
      items: {
        ip: "IP address",
        time: "Date and time of request",
        resource: "Requested page or resource",
        status: "HTTP status code",
        browser: "Browser type and version",
        os: "Operating system",
        referrer: "Referrer URL (previously visited page)",
      },
      purpose:
        "These data are used solely for technical monitoring, error analysis, and service security.",
      legalBasis:
        "Legal basis: Art. 6(1)(f) GDPR (legitimate interest in secure and stable operation).",
    },
    cookies: {
      title: "3. Cookies",
      description: "This website only uses technically necessary cookies.",
      items: {
        login: "Login function",
        session: "Session management (session cookies)",
      },
      noTracking:
        "These cookies do not contain tracking information and are not used for analytics or marketing.",
      legalBasis:
        "Legal basis: Art. 6(1)(b) GDPR (service delivery) and Art. 6(1)(f) GDPR (legitimate interest in secure operation).",
      noBanner:
        "Because only strictly necessary cookies are used, no separate cookie consent banner is required.",
    },
    email: {
      title: "4. Email communication",
      description:
        "If users provide an email address while using the service, it is used only for automated emails required to provide the service.",
      legalBasis:
        "Legal basis: Art. 6(1)(b) GDPR (performance of the requested service).",
    },
    sharing: {
      title: "5. Data sharing",
      description:
        "Personal data are generally not shared with third parties unless required by law or necessary for technical service delivery.",
    },
    retention: {
      title: "6. Storage duration",
      description:
        "Personal data are stored only as long as required for service provision or legal obligations.",
      logfiles: "Server log files are deleted regularly.",
    },
    rights: {
      title: "7. Rights of data subjects",
      items: {
        access: "Right of access (Art. 15 GDPR)",
        rectification: "Right to rectification (Art. 16 GDPR)",
        erasure: "Right to erasure (Art. 17 GDPR)",
        restriction: "Right to restriction of processing (Art. 18 GDPR)",
        portability: "Right to data portability (Art. 20 GDPR)",
        object: "Right to object (Art. 21 GDPR)",
      },
      contact:
        "To exercise these rights, contact the controller by email at any time.",
    },
    supervisory: {
      title: "8. Right to lodge a complaint",
      description:
        "Data subjects have the right to lodge a complaint with a data protection supervisory authority.",
      authority:
        "Competent authority in North Rhine-Westphalia: State Commissioner for Data Protection and Freedom of Information NRW (LDI NRW)",
    },
    back: "Back to home",
  },
  dashboard: {
    kicker: "Overview",
    title: "Job status at a glance",
    subtitle: "{active} active of {total} total jobs",
    loading: "Loading dashboard data...",
    empty:
      "No jobs configured yet. Create your first alert job to get started.",
    loadFailed: "Could not load dashboard jobs.",
    enabled: "Enabled",
    disabled: "Disabled",
    statusUnknown: "Unknown",
    actions: {
      openJobs: "Open jobs table",
      newJob: "New job",
      view: "View",
      edit: "Edit",
    },
    job: {
      station: "Station",
      limit: "Limit",
      state: "State",
      updated: "Last update",
      trend: "Pegel history (last 3 days)",
      latestValue: "Latest level: {value} cm",
      noRecentData: "No recent measured data available for the last 3 days.",
    },
    dataSource: "Measurements and station details are sourced from",
    stateValues: {
      no_crossing: "No crossing",
      crossing_incoming: "Crossing incoming",
      crossing_active: "Crossing active",
      crossing_soon_over: "Crossing ending soon",
    },
  },
  jobsList: {
    title: "Jobs",
    createJob: "Create job",
    includeDisabled: "Include disabled jobs",
    disabledSuccess: "The job was disabled successfully.",
    loadFailed: "Could not load jobs.",
    loading: "Loading jobs...",
    empty: "No jobs found.",
    confirmDelete: "Delete this job? It will be disabled (soft delete).",
    table: {
      name: "Name",
      station: "Station",
      limit: "Limit",
      locale: "Locale",
      status: "Status",
      actions: "Actions",
    },
    enabled: "Enabled",
    disabled: "Disabled",
    view: "View",
    edit: "Edit",
    delete: "Delete",
    deleting: "Deleting...",
  },
  jobForm: {
    createTitle: "Create job",
    editTitle: "Edit job",
    loadingJob: "Loading job...",
    jobNotFound: "Job not found.",
    fields: {
      name: "Name",
      station: "Station",
      stationPlaceholder: "Search stations by name, river, or UUID",
      limitCm: "Limit (cm)",
      locale: "Locale",
      localeGerman: "German (de)",
      localeEnglish: "English (en)",
      alertRecipient: "Service-alert-recipient",
      alertRecipientPlaceholder: "alerts{'@'}example.com",
      alertRecipientHint: "Used only for service down alerts.",
      recipients: "Alert-recipients (comma or newline separated)",
      recipientsPlaceholder:
        "alice{'@'}example.com, bob{'@'}example.com",
      recipientsHint:
        "Separate addresses with commas, semicolons, or new lines.",
      scheduleCron: "Time-schedule (5 fields)",
      scheduleCronPlaceholder: "*/15 * * * *",
      scheduleCronHint: "Format: minute hour day month weekday.",
      scheduleCronCheckInfo: "Defines how often Hochwasser is checked.",
      scheduleCronEditorError: "Time-schedule editor hint: {message}",
      repeatAlertsOnCheck: "Repeat alerts on check",
      repeatAlertsOnCheckHint:
        "Emails are always sent on state changes. Enable this to also send emails on every check while still in an alerting state.",
      moreInfo: "more info",
      enabled: "Enabled",
    },
    station: {
      loading: "Loading stations...",
      noMatch: "No matching station found.",
      selected: "Selected: {value}",
      detailUuid: "UUID: {value}",
      detailLongName: "Long name: {value}",
      detailWater: "Water: {value}",
      detailAgency: "Agency: {value}",
      detailNumber: "Number: {value}",
      detailKm: "KM: {value}",
      detailCoords: "Coords: {value}",
    },
    actions: {
      cancel: "Cancel",
      saveChanges: "Save changes",
      saveCreate: "Create job",
      saving: "Saving...",
    },
  },
  jobDetails: {
    titleFallback: "Job details",
    back: "Back",
    edit: "Edit",
    loadingJob: "Loading job...",
    jobNotFound: "Job not found.",
    fields: {
      station: "Station",
      water: "Water",
      agency: "Agency",
      coordinates: "Coordinates",
      stationUuid: "Station UUID",
      limit: "Limit",
      schedule: "Time-schedule",
      locale: "Locale",
      alertRecipient: "Service-alert-recipient",
      recipients: "Alert-recipients",
      statusTitle: "Status",
      state: "State",
      stateSince: "State since",
      predictedPeak: "Predicted peak",
      at: "at",
      lastNotified: "Last notified",
      na: "n/a",
    },
    enabled: "Enabled",
    disabled: "Disabled",
    status: {
      loading: "Loading status...",
      stateValues: {
        normal: "Normal",
        warn: "Warning",
        alarm: "Alarm",
      },
    },
    outbox: {
      title: "Outbox",
      limitOffset: "limit {limit} | offset {offset}",
      loading: "Loading outbox...",
      empty: "No outbox entries.",
      table: {
        id: "ID",
        target: "Target",
        reason: "Reason",
        status: "Status",
        attempts: "Attempts",
        nextAttempt: "Next attempt",
      },
      previous: "Previous",
      next: "Next",
      targetValues: {
        no_crossing: "No crossing",
        crossing_incoming: "Crossing incoming",
        crossing_active: "Crossing active",
        crossing_soon_over: "Crossing ending soon",
      },
      reasonValues: {
        transition: "Transition",
        repeat: "Repeat notification",
        worse_eta: "Earlier crossing forecast",
        worse_peak: "Higher peak forecast",
        worse_end: "Later end forecast",
      },
      statusValues: {
        pending: "Pending",
        queued: "Queued",
        sending: "Sending",
        sent: "Sent",
        delivered: "Delivered",
        failed: "Failed",
        dead: "Dead",
        cancelled: "Cancelled",
      },
    },
  },
  notFound: {
    title: "Page not found",
    description: "Try heading back to the start page.",
    action: "Go to start page",
  },
  validation: {
    nameRequired: "Name is required.",
    nameTooLong: "Name must be 120 characters or fewer.",
    stationUuidRequired: "Station UUID is required.",
    stationUuidTooLong: "Station UUID must be 120 characters or fewer.",
    alertRecipientRequired: "Service-alert-recipient is required.",
    alertRecipientTooLong:
      "Service-alert-recipient must be 254 characters or fewer.",
    alertRecipientInvalid:
      "Service-alert-recipient must be a valid email address.",
    recipientsRequired: "At least one recipient is required.",
    recipientsTooMany: "You can provide at most 25 recipients.",
    recipientsInvalidAddress: "Invalid recipient address: {email}",
    localeUnsupported: "Locale must be either German or English.",
    scheduleRequired: "Time-schedule is required.",
    scheduleInvalid: "Time-schedule must be a valid 5-field expression.",
    limitRequired: "Limit is required.",
    limitWholeNumber: "Limit must be a whole number between 0 and 100000.",
    limitRange: "Limit must be between 0 and 100000.",
  },
  api: {
    validationFailed: "Validation failed. Please review your input.",
    authRequired: "Authentication required. Please sign in again.",
    actionNotAllowed: "You are not allowed to perform this action.",
    requestFailedStatus: "API request failed with status {status}",
  },
} as const;

export default en;
