type RecognitionAlternative = { transcript: string };
type RecognitionResult = { 0?: RecognitionAlternative };
type RecognitionEvent = { results: RecognitionResult[] };

interface Recognition extends EventTarget {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start(): void;
  stop(): void;
  onresult: ((event: RecognitionEvent) => void) | null;
  onerror: ((event: Event) => void) | null;
  onend: (() => void) | null;
  onstart: (() => void) | null;
}

type SpeechRecognitionConstructor = new () => Recognition;

function getSpeechRecognitionConstructor(): SpeechRecognitionConstructor | null {
  const speechWindow = window as typeof window & {
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
    SpeechRecognition?: SpeechRecognitionConstructor;
  };
  return speechWindow.webkitSpeechRecognition ?? speechWindow.SpeechRecognition ?? null;
}

export function startSTT(onText: (t: string) => void, opts: { lang?: string; debug?: boolean } = {}) {
  const SR = getSpeechRecognitionConstructor();
  if (!SR) {
    alert("SpeechRecognition not supported in this browser.");
    return () => {};
  }

  const rec: Recognition = new SR();
  rec.continuous = false;
  rec.interimResults = false;
  rec.lang = opts.lang || "en-US";

  rec.onresult = (event: RecognitionEvent) => {
    try {
      const txt = event.results?.[0]?.[0]?.transcript;
      if (opts.debug) console.debug("STT result", event);
      if (txt) onText(txt.trim());
    } catch (err) {
      if (opts.debug) console.error("STT result error", err);
    }
  };

  rec.onerror = (event: Event) => {
    if (opts.debug) console.error("STT error", event);
  };

  rec.onend = () => {
    if (opts.debug) console.debug("STT ended");
  };

  try {
    rec.start();
    if (opts.debug) console.debug("STT started", { lang: rec.lang });
  } catch (err: unknown) {
    if (opts.debug) console.error("STT start failed", err);
  }

  return () => {
    try {
      rec.stop();
      if (opts.debug) console.debug("STT stopped");
    } catch (err: unknown) {
      if (opts.debug) console.error("STT stop failed", err);
    }
  };
}

type StatusHandler = (status: "start" | "stop" | "error") => void;

let activeRecognition: Recognition | null = null;
let activeStopped = false;
let activeStatusHandler: StatusHandler | undefined;
let activeDebug = false;
let restartTimeout: number | undefined;

function clearRestartTimer() {
  if (restartTimeout !== undefined) {
    window.clearTimeout(restartTimeout);
    restartTimeout = undefined;
  }
}

export function startContinuousSTT(options: {
  onText: (t: string) => void;
  onStatus?: StatusHandler;
  lang?: string;
  debug?: boolean;
}) {
  const SR = getSpeechRecognitionConstructor();
  if (!SR) {
    alert("SpeechRecognition not supported in this browser.");
    return { stop: () => {} };
  }

  if (activeRecognition) {
    stopContinuousSTT();
  }

  const rec: Recognition = new SR();
  rec.continuous = true;
  rec.interimResults = false;
  rec.lang = options.lang || "en-US";

  activeRecognition = rec;
  activeStopped = false;
  activeStatusHandler = options.onStatus;
  activeDebug = Boolean(options.debug);

  rec.onstart = () => {
    if (activeDebug) console.debug("Continuous STT start");
    activeStatusHandler?.("start");
  };

  rec.onresult = (event: RecognitionEvent) => {
    try {
      const txt = event.results?.[0]?.[0]?.transcript;
      if (activeDebug) console.debug("Continuous STT result", event);
      if (txt) options.onText(txt.trim());
    } catch (err) {
      if (activeDebug) console.error("Continuous STT result error", err);
    }
  };

  rec.onerror = (event: Event) => {
    if (activeDebug) console.error("Continuous STT error", event);
    activeStatusHandler?.("error");
  };

  rec.onend = () => {
    if (activeDebug) console.debug("Continuous STT ended");
    if (activeStopped) {
      activeStatusHandler?.("stop");
      return;
    }
    clearRestartTimer();
    restartTimeout = window.setTimeout(() => {
      if (activeStopped) return;
      try {
        rec.start();
      } catch (err) {
        if (activeDebug) console.error("Continuous STT restart failed", err);
        activeStatusHandler?.("error");
        activeStopped = true;
      }
    }, 250);
  };

  try {
    rec.start();
    if (activeDebug) console.debug("Continuous STT started", { lang: rec.lang });
  } catch (err) {
    if (activeDebug) console.error("Continuous STT start failed", err);
    activeStatusHandler?.("error");
    activeRecognition = null;
  }

  return {
    stop() {
      stopContinuousSTT();
    },
  };
}

export function stopContinuousSTT() {
  if (!activeRecognition) return;
  activeStopped = true;
  clearRestartTimer();
  try {
    activeRecognition.stop();
  } catch (err) {
    if (activeDebug) console.error("Continuous STT stop failed", err);
  }
  activeStatusHandler?.("stop");
  activeRecognition = null;
  activeStatusHandler = undefined;
}

export function speak(text: string, opts: { lang?: string; pitch?: number; rate?: number; debug?: boolean } = {}) {
  if (!("speechSynthesis" in window)) {
    if (opts.debug) console.warn("SpeechSynthesis not supported");
    return;
  }

  const u = new SpeechSynthesisUtterance(text);
  if (opts.lang) u.lang = opts.lang;
  if (opts.pitch !== undefined) u.pitch = opts.pitch;
  if (opts.rate !== undefined) u.rate = opts.rate;

  if (opts.debug) {
    u.onstart = () => console.debug("TTS start", { text });
    u.onend = () => console.debug("TTS end");
    u.onerror = (e) => console.error("TTS error", e);
  }

  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(u);
}
