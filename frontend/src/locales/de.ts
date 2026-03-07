const de = {
  shell: {
    appName: "Hochwasser",
    appSection: "Einsatz-Dashboard",
    nav: {
      overview: "Dashboard",
      jobs: "Jobs",
    },
    actions: {
      signOut: "Abmelden",
    },
    locale: {
      label: "Sprache",
      de: "DE",
      en: "EN",
    },
    footer: {
      source:
        "Datenquellen und Stationsmetadaten stammen aus offiziellen öffentlichen Quellen.",
      imprint: "Impressum",
      privacy: "Datenschutzerklärung",
    },
  },
  auth: {
    login: {
      title: "Willkommen zurück",
      email: "E-Mail",
      password: "Passwort",
      hidePassword: "Passwort ausblenden",
      showPassword: "Passwort anzeigen",
      submit: "Anmelden",
      submitting: "Melde an...",
      newHere: "Neu hier?",
      createAccount: "Konto erstellen",
      cancel: "Abbrechen",
      close: "Login-Dialog schließen",
      failedFallback: "Anmeldung fehlgeschlagen. Bitte erneut versuchen.",
    },
    register: {
      title: "Konto erstellen",
      email: "E-Mail",
      password: "Passwort",
      confirmPassword: "Passwort bestätigen",
      hidePassword: "Passwort ausblenden",
      showPassword: "Passwort anzeigen",
      hideConfirmPassword: "Bestätigung ausblenden",
      showConfirmPassword: "Bestätigung anzeigen",
      submit: "Konto erstellen",
      submitting: "Erstelle Konto...",
      backToLogin: "Zurück zum Login",
      passwordsMismatch: "Passwörter stimmen nicht überein.",
      createdCheckInbox:
        "Konto erstellt. Bitte E-Mails prüfen, Adresse bestätigen und dann anmelden.",
      failedFallback: "Registrierung fehlgeschlagen. Bitte erneut versuchen.",
    },
  },
  landing: {
    kicker: "Frühwarn-Workspace für Hochwasser",
    title:
      "Beobachte deine Pegel und reagiere, bevor Grenzwerte kritisch werden.",
    copy: "Hochwasser Alarm verbindet offizielle Stationsdaten, Schwellwert-Alarmierung und praktische Job-Steuerung in einem fokussierten Dashboard.",
    actions: {
      signIn: "Anmelden",
      createAccount: "Konto erstellen",
      openDashboard: "Dashboard öffnen",
      startNow: "Jetzt starten",
      imprint: "Impressum",
      privacy: "Datenschutz",
    },
    features: {
      alerting: {
        title: "Grenzwert-Alarme mit klarem Fokus",
        copy: "Konfiguriere Jobs pro Station, setze klare Limits und reduziere unnötigen Alarm-Lärm.",
      },
      monitoring: {
        title: "Operativer Live-Überblick",
        copy: "Sieh Status, Trends und Kontext pro Job auf einen Blick für schnellere Entscheidungen.",
      },
      sources: {
        title: "Integration offizieller Quellen",
        copy: "Stations- und Pegeldaten werden über offizielle öffentliche Anbieter bereitgestellt.",
      },
    },
    footer: {
      source:
        "Nur zur Information. Offizielle Warnungen und Einsatzanweisungen haben immer Vorrang.",
    },
  },
  imprint: {
    kicker: "Rechtliche Angaben",
    title: "Impressum",
    subtitle: "Angaben gemäß §5 Digitale-Dienste-Gesetz (DDG)",
    section: {
      provider: "Anbieter",
      contact: "Kontakt",
      disclaimer: "Haftungs- und Nutzungshinweis",
    },
    person: "Michael Breyer",
    addressLine1: "Siebengebirgsallee 51",
    addressLine2: "50939 Köln",
    country: "Deutschland",
    emailLabel: "E-Mail:",
    disclaimer: {
      source:
        "Pegel- und Stationsdaten stammen aus offiziellen öffentlichen Schnittstellen. Dieses Projekt beansprucht keine Eigentumsrechte an diesen Daten.",
      informational:
        "Der Dienst dient nur zur Information und ersetzt keine offiziellen Warnungen, Notfallmeldungen oder Behördenanweisungen.",
      noGuarantee:
        "Es gibt keine Gewähr für Verfügbarkeit, Korrektheit, Vollständigkeit, Aktualität oder Zustellung von Alarmen.",
      liability:
        "Der Betreiber haftet nicht für Schäden durch verspätete, fehlende oder fehlerhafte Alarme.",
    },
    back: "Zur Startseite",
  },
  privacy: {
    title: "Datenschutzerklärung",
    controller: {
      title: "1. Verantwortlicher",
      person: "Michael Breyer",
      addressLine1: "Siebengebirgsallee 51",
      addressLine2: "50939 Köln",
      country: "Deutschland",
      emailLabel: "E-Mail:",
    },
    logfiles: {
      title: "2. Server-Logfiles",
      description:
        "Beim Aufruf dieser Website werden automatisch Informationen durch den Webserver erfasst und in sogenannten Server-Logfiles gespeichert.",
      items: {
        ip: "IP-Adresse",
        time: "Datum und Uhrzeit der Anfrage",
        resource: "aufgerufene Seite bzw. Ressource",
        status: "HTTP-Statuscode",
        browser: "Browsertyp und Browserversion",
        os: "Betriebssystem",
        referrer: "Referrer-URL (die zuvor besuchte Seite)",
      },
      purpose:
        "Diese Daten dienen ausschließlich der technischen Überwachung, der Fehleranalyse und der Sicherheit des Dienstes.",
      legalBasis:
        "Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse an einem sicheren und stabilen Betrieb der Website).",
    },
    cookies: {
      title: "3. Cookies",
      description:
        "Diese Website verwendet ausschließlich technisch notwendige Cookies.",
      items: {
        login: "Login-Funktion",
        session: "Sitzungsverwaltung (Session-Cookies)",
      },
      noTracking:
        "Diese Cookies enthalten keine Tracking-Informationen und werden nicht zu Analyse- oder Marketingzwecken verwendet.",
      legalBasis:
        "Die Verarbeitung erfolgt auf Grundlage von Art. 6 Abs. 1 lit. b DSGVO sowie Art. 6 Abs. 1 lit. f DSGVO.",
      noBanner:
        "Da ausschließlich technisch notwendige Cookies verwendet werden, ist kein separates Cookie-Banner erforderlich.",
    },
    email: {
      title: "4. E-Mail-Kommunikation",
      description:
        "Wenn Nutzer ihre E-Mail-Adresse im Rahmen der Nutzung des Dienstes angeben, wird diese ausschließlich zum automatisierten Versand dienstrelevanter E-Mails verwendet.",
      legalBasis:
        "Die Verarbeitung erfolgt auf Grundlage von Art. 6 Abs. 1 lit. b DSGVO.",
    },
    sharing: {
      title: "5. Weitergabe von Daten",
      description:
        "Eine Weitergabe personenbezogener Daten an Dritte findet grundsätzlich nicht statt, sofern dies nicht gesetzlich vorgeschrieben ist oder zur technischen Bereitstellung des Dienstes erforderlich wird.",
    },
    retention: {
      title: "6. Speicherdauer",
      description:
        "Personenbezogene Daten werden nur so lange gespeichert, wie dies für die Bereitstellung des Dienstes oder aus rechtlichen Gründen erforderlich ist.",
      logfiles: "Server-Logfiles werden regelmäßig gelöscht.",
    },
    rights: {
      title: "7. Rechte der betroffenen Personen",
      items: {
        access:
          "Recht auf Auskunft über gespeicherte personenbezogene Daten (Art. 15 DSGVO)",
        rectification:
          "Recht auf Berichtigung unrichtiger Daten (Art. 16 DSGVO)",
        erasure: "Recht auf Löschung (Art. 17 DSGVO)",
        restriction: "Recht auf Einschränkung der Verarbeitung (Art. 18 DSGVO)",
        portability: "Recht auf Datenübertragbarkeit (Art. 20 DSGVO)",
        object: "Recht auf Widerspruch gegen die Verarbeitung (Art. 21 DSGVO)",
      },
      contact:
        "Zur Ausübung dieser Rechte kann jederzeit eine E-Mail an den oben genannten Verantwortlichen gesendet werden.",
    },
    supervisory: {
      title: "8. Beschwerderecht bei einer Aufsichtsbehörde",
      description:
        "Betroffene haben das Recht, sich bei einer Datenschutz-Aufsichtsbehörde über die Verarbeitung ihrer personenbezogenen Daten zu beschweren.",
      authority:
        "Zuständige Aufsichtsbehörde in Nordrhein-Westfalen: Landesbeauftragte für Datenschutz und Informationsfreiheit Nordrhein-Westfalen (LDI NRW)",
    },
    back: "Zur Startseite",
  },
  dashboard: {
    kicker: "Übersicht",
    title: "Job-Status auf einen Blick",
    subtitle: "{active} aktive von {total} Jobs",
    loading: "Lade Dashboard-Daten...",
    empty: "Noch keine Jobs angelegt. Erstelle deinen ersten Alarm-Job.",
    loadFailed: "Dashboard-Jobs konnten nicht geladen werden.",
    enabled: "Aktiv",
    disabled: "Deaktiviert",
    statusUnknown: "Unbekannt",
    actions: {
      openJobs: "Job-Tabelle öffnen",
      newJob: "Neuer Job",
      view: "Ansehen",
      edit: "Bearbeiten",
    },
    job: {
      station: "Station",
      limit: "Grenzwert",
      state: "Zustand",
      updated: "Letztes Update",
      trend: "Pegelverlauf (letzte 3 Tage, keine Prognose)",
      latestValue: "Letzter Pegel: {value} cm",
      noRecentData: "Keine gemessenen Werte für die letzten 3 Tage verfügbar.",
    },
    dataSource: "Messwerte und Stationsdetails stammen von",
    stateValues: {
      no_crossing: "Keine Überschreitung",
      crossing_incoming: "Überschreitung bevorstehend",
      crossing_active: "Überschreitung aktiv",
      crossing_soon_over: "Überschreitung endet bald",
    },
  },
  jobsList: {
    title: "Jobs",
    createJob: "Job erstellen",
    includeDisabled: "Deaktivierte Jobs einbeziehen",
    disabledSuccess: "Der Job wurde erfolgreich deaktiviert.",
    loadFailed: "Jobs konnten nicht geladen werden.",
    loading: "Lade Jobs...",
    empty: "Keine Jobs gefunden.",
    confirmDelete: "Diesen Job löschen? Er wird nur deaktiviert (Soft Delete).",
    table: {
      name: "Name",
      station: "Station",
      limit: "Grenzwert",
      locale: "Sprache",
      status: "Status",
      actions: "Aktionen",
    },
    enabled: "Aktiv",
    disabled: "Deaktiviert",
    view: "Ansehen",
    edit: "Bearbeiten",
    delete: "Löschen",
    deleting: "Lösche...",
  },
  jobForm: {
    createTitle: "Job erstellen",
    editTitle: "Job bearbeiten",
    loadingJob: "Lade Job...",
    jobNotFound: "Job nicht gefunden.",
    fields: {
      name: "Name",
      station: "Station",
      stationPlaceholder: "Station nach Name, Fluss oder UUID suchen",
      limitCm: "Grenzwert (cm)",
      locale: "Sprache",
      localeGerman: "Deutsch (de)",
      localeEnglish: "Englisch (en)",
      alertRecipient: "Service-Alarm-Empfänger",
      alertRecipientPlaceholder: "alarme{'@'}beispiel.de",
      alertRecipientHint: "Wird nur für Service-Down-Alarme verwendet.",
      recipients: "Alarm-Empfänger (durch Komma oder Zeilenumbruch getrennt)",
      recipientsPlaceholder:
        "alice{'@'}example.com, bob{'@'}example.com",
      recipientsHint:
        "Adressen mit Kommas, Semikolons oder Zeilenumbrüchen trennen.",
      scheduleCron: "Zeitplan (5 Felder)",
      scheduleCronPlaceholder: "*/15 * * * *",
      scheduleCronHint: "Format: Minute Stunde Tag Monat Wochentag.",
      scheduleCronCheckInfo: "Legt fest, wie oft Hochwasser geprüft wird.",
      scheduleCronEditorError: "Zeitplan-Editor Hinweis: {message}",
      repeatAlertsOnCheck: "Alarme bei jedem Check wiederholen",
      repeatAlertsOnCheckHint:
        "E-Mails werden immer bei Zustandswechseln gesendet. Aktivieren Sie dies, um zusätzlich bei jedem Check im Alarmzustand E-Mails zu senden.",
      moreInfo: "mehr Infos",
      enabled: "Aktiv",
    },
    station: {
      loading: "Lade Stationen...",
      noMatch: "Keine passende Station gefunden.",
      selected: "Ausgewählt: {value}",
      detailUuid: "UUID: {value}",
      detailLongName: "Langname: {value}",
      detailWater: "Gewässer: {value}",
      detailAgency: "Behörde: {value}",
      detailNumber: "Nummer: {value}",
      detailKm: "KM: {value}",
      detailCoords: "Koordinaten: {value}",
    },
    actions: {
      cancel: "Abbrechen",
      saveChanges: "Änderungen speichern",
      saveCreate: "Job erstellen",
      saving: "Speichere...",
    },
  },
  jobDetails: {
    titleFallback: "Job-Details",
    back: "Zurück",
    edit: "Bearbeiten",
    loadingJob: "Lade Job...",
    jobNotFound: "Job nicht gefunden.",
    fields: {
      station: "Station",
      water: "Gewässer",
      agency: "Behörde",
      coordinates: "Koordinaten",
      stationUuid: "Stations-UUID",
      limit: "Grenzwert",
      schedule: "Zeitplan",
      locale: "Sprache",
      alertRecipient: "Service-Alarm-Empfänger",
      recipients: "Alarm-Empfänger",
      statusTitle: "Status",
      state: "Zustand",
      stateSince: "Zustand seit",
      predictedPeak: "Prognostizierter Peak",
      at: "um",
      lastNotified: "Zuletzt benachrichtigt",
      na: "k. A.",
    },
    enabled: "Aktiv",
    disabled: "Deaktiviert",
    status: {
      loading: "Lade Status...",
      stateValues: {
        normal: "Normal",
        warn: "Warnung",
        alarm: "Alarm",
      },
    },
    outbox: {
      title: "Outbox",
      limitOffset: "Limit {limit} | Offset {offset}",
      loading: "Lade Outbox...",
      empty: "Keine Outbox-Einträge.",
      table: {
        id: "ID",
        target: "Ziel",
        reason: "Grund",
        status: "Status",
        attempts: "Versuche",
        nextAttempt: "Nächster Versuch",
      },
      previous: "Zurück",
      next: "Weiter",
      targetValues: {
        no_crossing: "Keine Überschreitung",
        crossing_incoming: "Überschreitung bevorstehend",
        crossing_active: "Überschreitung aktiv",
        crossing_soon_over: "Überschreitung endet bald",
      },
      reasonValues: {
        transition: "Zustandswechsel",
        repeat: "Wiederholte Benachrichtigung",
        worse_eta: "Frühere Überschreitungsprognose",
        worse_peak: "Höhere Spitzenprognose",
        worse_end: "Spätere Entwarnungsprognose",
      },
      statusValues: {
        pending: "Ausstehend",
        queued: "In Warteschlange",
        sending: "Wird gesendet",
        sent: "Gesendet",
        delivered: "Zugestellt",
        failed: "Fehlgeschlagen",
        dead: "Endgültig fehlgeschlagen",
        cancelled: "Abgebrochen",
      },
    },
  },
  notFound: {
    title: "Seite nicht gefunden",
    description: "Zurück zur Startseite gehen.",
    action: "Zur Startseite",
  },
  validation: {
    nameRequired: "Name ist erforderlich.",
    nameTooLong: "Name darf höchstens 120 Zeichen haben.",
    stationUuidRequired: "Stations-UUID ist erforderlich.",
    stationUuidTooLong: "Stations-UUID darf höchstens 120 Zeichen haben.",
    alertRecipientRequired: "Service-Alarm-Empfänger ist erforderlich.",
    alertRecipientTooLong:
      "Service-Alarm-Empfänger darf höchstens 254 Zeichen haben.",
    alertRecipientInvalid:
      "Service-Alarm-Empfänger muss eine gültige E-Mail-Adresse sein.",
    recipientsRequired: "Mindestens ein Empfänger ist erforderlich.",
    recipientsTooMany: "Es sind maximal 25 Empfänger erlaubt.",
    recipientsInvalidAddress: "Ungültige Empfänger-Adresse: {email}",
    localeUnsupported: "Sprache muss Deutsch oder Englisch sein.",
    scheduleRequired: "Zeitplan ist erforderlich.",
    scheduleInvalid: "Zeitplan muss ein gültiger Ausdruck mit 5 Feldern sein.",
    limitRequired: "Grenzwert ist erforderlich.",
    limitWholeNumber:
      "Grenzwert muss eine ganze Zahl zwischen 0 und 100000 sein.",
    limitRange: "Grenzwert muss zwischen 0 und 100000 liegen.",
  },
  api: {
    validationFailed: "Validierung fehlgeschlagen. Bitte Eingaben prüfen.",
    authRequired: "Authentifizierung erforderlich. Bitte erneut anmelden.",
    actionNotAllowed: "Sie dürfen diese Aktion nicht ausführen.",
    requestFailedStatus: "API-Anfrage mit Status {status} fehlgeschlagen",
  },
} as const;

export default de;
