const en = {
  shell: {
    appName: "Pegel-Alarm",
    appSection: "Your Alert Center",
    nav: {
      overview: "Dashboard",
      account: "Account",
      jobs: "Alerts",
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
  account: {
    title: "Account & Security",
    subtitle: "Manage your password, account deletion, and current usage limits.",
    limits: {
      activeJobs: "Active alerts: {current} of {max}",
      maxRecipients: "Maximum recipients per alert: {max}",
    },
    password: {
      title: "Change password",
      current: "Current password",
      new: "New password",
      confirm: "Confirm new password",
      submit: "Update password",
      success: "Password updated successfully.",
      errors: {
        mismatch: "The new passwords do not match.",
        minLength: "The new password must be at least 8 characters long.",
        failed: "Password could not be updated.",
      },
    },
    delete: {
      title: "Delete account",
      warning:
        "Warning: This action permanently removes your account and associated data.",
      instructions:
        "Type DELETE in the field to confirm. Your account will then be permanently deleted.",
      confirmLabel: "Confirmation",
      submit: "Permanently delete account",
      failed: "Account could not be deleted.",
    },
  },
  donation: {
    cta: "Buy me a coffee",
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
        "If the address can be used, we will send an email with next steps.",
      failedFallback:
        "Registration received. If the address can be used, we will send an email with next steps.",
      rateLimited:
        "Too many registration attempts. Please wait {minutes} minutes and try again.",
    },
  },
  charts: {
    hydrograph: {
      measured: "Measured",
      forecast: "Forecast",
      limit: "Limit",
      unitCm: "cm",
      ariaLabel: "Hydrograph with measured and forecast values",
      empty: "No measured or forecast values are currently available.",
    },
  },
  landing: {
    kicker: "Simple flood alerts for everyone",
    title: "Get email alerts before water levels become critical.",
    copy: "Choose a station, set your limit, and receive automatic notifications. This helps you react early when the situation gets serious.",
    freeParagraph: "The service is completely free to use.",
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
        title: "Clear alerts, less noise",
        copy: "Set your own level threshold per station and receive messages when it truly matters.",
      },
      monitoring: {
        title: "See everything at a glance",
        copy: "The dashboard shows current levels, trends, and alert status in a way non-technical users can understand.",
      },
      sources: {
        title: "Data from Pegelonline",
        copy: "We source station and water-level data directly from Pegelonline (WSV).",
      },
    },
    steps: {
      pickStation: {
        title: "Pick a station",
        copy: "Search by station name or river and select the right measuring point.",
      },
      setLimit: {
        title: "Set your limit",
        copy: "Define the water level in centimeters where you want to be alerted.",
      },
      getAlert: {
        title: "Receive email alerts",
        copy: "You get notified automatically when the level crosses your limit or the outlook gets worse.",
      },
    },
    example: {
      kicker: "Preview",
      title: "See the live graph and map interaction",
      copy: "The Cologne station is preselected. Pick any marker in the map and the example graph updates instantly.",
      retry: "Try again",
      loadFailedGeneric: "The example data could not be loaded right now.",
      seriesLoading: "Loading chart and email preview data...",
      seriesUnavailable: "No measured or forecast values are available for this station yet.",
      mapLoading: "Loading station map...",
      mapUnavailable: "The station map is currently unavailable.",
      mapAriaLabel: "Interactive map of gauge stations",
      rerollLimitAriaLabel: "Generate another sample threshold value",
      loading: "Loading station...",
      limitLabel: "Limit:",
      state: "State: {value}",
      stationCount: "Stations on map: {value}",
      mapHint: "Click a station point to update the example hydrograph.",
      stateValues: {
        no_crossing: "No crossing",
        crossing_incoming: "Crossing incoming",
        crossing_active: "Crossing active",
        crossing_soon_over: "Crossing ending soon",
      },
      email: {
        previewTitle: "Example email",
        fromLabel: "From:",
        toLabel: "To:",
        subjectLabel: "Subject:",
        subject: "[Flood Alert] {station}: {limit} {unit} reached",
        sectionStationInformation: "Station information",
        sectionAlertContext: "Alert context",
        stationNumberLine: "Station number: {value}",
        longNameLine: "Long name: {value}",
        waterBodyLine: "Water body: {value}",
        thresholdLine: "Threshold: {value} cm",
        currentValueLine: "Current value: {value} (at {time})",
        triggerSourceLine: "Trigger source: {value}",
        triggerTimeLine: "Trigger time: {value}",
        maxForecastLine: "Maximum forecast value: {value} (at {time})",
        triggerSourceCurrent: "current",
        triggerSourceOfficial: "official",
        introValues: {
          no_crossing:
            "No threshold crossing is expected right now. We will notify you as soon as the outlook worsens.",
          crossing_incoming:
            "The forecast indicates an upcoming threshold crossing. Please monitor the situation closely.",
          crossing_active:
            "The threshold is already reached or exceeded in this example. This mirrors an active alert email.",
          crossing_soon_over:
            "The threshold is still exceeded at the moment, but the forecast suggests the situation will calm soon.",
        },
      },
    },
    footer: {
      source:
        "Informational support only. Always follow official warnings and emergency guidance.",
      free: "The service is free to use.",
      donate:
        "If the free service helps you, consider a small donation to support hosting and further development.",
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
    addressLine1: "Siebengebirgsallee 51",
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
      addressLine1: "Siebengebirgsallee 51",
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
    title: "Alert status at a glance",
    subtitle: "{active} active of {total} total alerts",
    loading: "Loading dashboard data...",
    empty:
      "No alerts configured yet. Create your first alert to get started.",
    loadFailed: "Could not load dashboard alerts.",
    enabled: "Enabled",
    disabled: "Disabled",
    statusUnknown: "Unknown",
    actions: {
      openJobs: "Open alerts list",
      newJob: "New alert",
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
    title: "Alerts",
    createJob: "Create alert",
    includeDisabled: "Include disabled alerts",
    disabledSuccess: "The alert was disabled successfully.",
    loadFailed: "Could not load alerts.",
    loading: "Loading alerts...",
    empty: "No alerts found.",
    confirmDelete: "Delete this alert? It will be disabled (soft delete).",
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
    createTitle: "Create alert",
    editTitle: "Edit alert",
    loadingJob: "Loading alert...",
    jobNotFound: "Alert not found.",
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
      scheduleCron: "Check interval",
      scheduleCronPlaceholder: "0 7,13,18 * * *",
      scheduleCronHint:
        "Optional as cron expression (minute hour day month weekday).",
      scheduleCronCheckInfo: "Defines how often new water levels are checked.",
      scheduleCronEditorError: "Interval editor hint: {message}",
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
      saveCreate: "Create alert",
      saving: "Saving...",
    },
  },
  jobDetails: {
    titleFallback: "Alert details",
    back: "Back",
    edit: "Edit",
    loadingJob: "Loading alert...",
    jobNotFound: "Alert not found.",
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
    hydrograph: {
      title: "Hydrograph with prediction",
      copy: "Measured values (solid), forecast values (dashed), and your threshold are shown together.",
    },
  },
  notFound: {
    title: "Page not found",
    description: "Try heading back to the start page.",
    action: "Go to start page",
  },
  seo: {
    routes: {
      landing: {
        title: "Flood Alerts by Email",
        description:
          "Pegel-Alarm monitors official river gauge data and sends email alerts when your threshold is reached.",
      },
      login: {
        title: "Sign In",
        description: "Sign in to manage your flood alert jobs and account settings.",
      },
      register: {
        title: "Create Account",
        description:
          "Create your free Pegel-Alarm account and start monitoring water levels with automatic alerts.",
      },
      imprint: {
        title: "Imprint",
        description: "Legal notice and provider details for Pegel-Alarm.",
      },
      privacy: {
        title: "Privacy Policy",
        description: "How Pegel-Alarm processes personal data and protects your privacy.",
      },
      app: {
        description: "Manage your water-level alert jobs in the Pegel-Alarm application.",
      },
      notFound: {
        title: "Page Not Found",
        description: "This page does not exist on Pegel-Alarm.",
      },
    },
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
    recipientsTooMany: "You can provide at most 5 recipients.",
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
