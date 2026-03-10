const de = {
  shell: {
    appName: "Pegel-Alarm",
    appSection: "Deine Alarmzentrale",
    nav: {
      overview: "Dashboard",
      account: "Konto",
      jobs: "Alarme",
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
        "Messdaten und Stationsinfos stammen aus offiziellen öffentlichen Quellen.",
      imprint: "Impressum",
      privacy: "Datenschutzerklärung",
    },
  },
  account: {
    title: "Konto & Sicherheit",
    subtitle: "Verwalte dein Passwort, Kontolöschung und aktuelle Nutzungsgrenzen.",
    limits: {
      activeJobs: "Aktive Alarme: {current} von {max}",
      maxRecipients: "Maximale Alarm-Empfänger pro Alarm: {max}",
    },
    password: {
      title: "Passwort ändern",
      current: "Aktuelles Passwort",
      new: "Neues Passwort",
      confirm: "Neues Passwort bestätigen",
      submit: "Passwort aktualisieren",
      success: "Passwort erfolgreich aktualisiert.",
      errors: {
        mismatch: "Die neuen Passwörter stimmen nicht überein.",
        minLength: "Das neue Passwort muss mindestens 8 Zeichen lang sein.",
        failed: "Passwort konnte nicht aktualisiert werden.",
      },
    },
    delete: {
      title: "Konto löschen",
      warning:
        "Achtung: Diese Aktion entfernt dein Konto und deine zugehörigen Daten dauerhaft.",
      instructions:
        "Gib zur Bestätigung DELETE in das Feld ein. Danach wird dein Konto endgültig gelöscht.",
      confirmLabel: "Bestätigung",
      submit: "Konto endgültig löschen",
      failed: "Konto konnte nicht gelöscht werden.",
    },
  },
  donation: {
    cta: "Projekt unterstützen",
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
        "Wenn die Adresse verwendet werden kann, senden wir dir eine E-Mail mit den nächsten Schritten.",
      failedFallback:
        "Registrierung entgegengenommen. Wenn die Adresse verwendet werden kann, senden wir dir eine E-Mail mit den nächsten Schritten.",
      rateLimited:
        "Zu viele Registrierungsversuche. Bitte warte {minutes} Minuten und versuche es erneut.",
    },
  },
  landing: {
    kicker: "Einfacher Pegel-Alarm für alle",
    title: "Du bekommst E-Mails, wenn dein Pegel kritisch wird.",
    copy: "Wähle eine Messstation, lege einen Grenzwert fest und erhalte automatische Benachrichtigungen. So weißt du frühzeitig, wenn Handlungsbedarf entsteht.",
    freeParagraph: "Der Service ist für dich komplett kostenfrei.",
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
        title: "Klare Alarme statt Zahlenchaos",
        copy: "Du legst je Station deinen Grenzwert fest und bekommst nur dann eine Nachricht, wenn es wirklich wichtig ist.",
      },
      monitoring: {
        title: "Alles auf einen Blick",
        copy: "Im Dashboard siehst du aktuelle Pegel, Trends und den Status deiner Alarme in verständlicher Form.",
      },
      sources: {
        title: "Offizielle Daten",
        copy: "Die Pegel- und Stationsdaten beziehen wir direkt von Pegelonline (WSV).",
      },
    },
    steps: {
      pickStation: {
        title: "Station auswählen",
        copy: "Suche deine Messstation nach Name oder Gewässer und wähle sie aus.",
      },
      setLimit: {
        title: "Grenzwert festlegen",
        copy: "Definiere den Pegel in Zentimetern, ab dem du gewarnt werden willst.",
      },
      getAlert: {
        title: "E-Mail erhalten",
        copy: "Wenn der Pegel den Wert erreicht oder sich die Lage verschärft, wirst du automatisch informiert.",
      },
    },
    footer: {
      source:
        "Nur zur Information: Offizielle Warnungen und Anweisungen von Behörden haben immer Vorrang.",
      free: "Die Nutzung ist kostenlos.",
      donate:
        "Wenn dir der kostenfreie Dienst hilft, freue ich mich über eine kleine Spende für Betrieb und Weiterentwicklung.",
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
    title: "Status deiner Alarme auf einen Blick",
    subtitle: "{active} aktive von {total} Alarmen",
    loading: "Lade Dashboard-Daten...",
    empty: "Du hast noch keinen Alarm erstellt. Lege jetzt deinen ersten Alarm an.",
    loadFailed: "Die Alarme für das Dashboard konnten nicht geladen werden.",
    enabled: "Aktiv",
    disabled: "Deaktiviert",
    statusUnknown: "Unbekannt",
    actions: {
      openJobs: "Alarmliste öffnen",
      newJob: "Neuer Alarm",
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
    title: "Alarme",
    createJob: "Alarm erstellen",
    includeDisabled: "Deaktivierte Alarme einbeziehen",
    disabledSuccess: "Der Alarm wurde erfolgreich deaktiviert.",
    loadFailed: "Alarme konnten nicht geladen werden.",
    loading: "Lade Alarme...",
    empty: "Keine Alarme gefunden.",
    confirmDelete:
      "Diesen Alarm löschen? Er wird nur deaktiviert (Soft Delete).",
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
    createTitle: "Alarm erstellen",
    editTitle: "Alarm bearbeiten",
    loadingJob: "Lade Alarm...",
    jobNotFound: "Alarm nicht gefunden.",
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
      scheduleCron: "Prüfintervall",
      scheduleCronPlaceholder: "0 7,13,18 * * *",
      scheduleCronHint:
        "Optional als Cron-Ausdruck (Minute Stunde Tag Monat Wochentag).",
      scheduleCronCheckInfo:
        "Legt fest, wie oft auf neue Pegelwerte geprüft wird.",
      scheduleCronEditorError: "Hinweis aus dem Intervall-Editor: {message}",
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
      saveCreate: "Alarm erstellen",
      saving: "Speichere...",
    },
  },
  jobDetails: {
    titleFallback: "Alarm-Details",
    back: "Zurück",
    edit: "Bearbeiten",
    loadingJob: "Lade Alarm...",
    jobNotFound: "Alarm nicht gefunden.",
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
    recipientsTooMany: "Es sind maximal 5 Empfänger erlaubt.",
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
