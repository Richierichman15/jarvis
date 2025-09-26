export function startSTT(onText: (t: string) => void, opts: { lang?: string; debug?: boolean } = {}) {
  const SR: any = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
  if (!SR) {
    alert("SpeechRecognition not supported in this browser.");
    return () => {};
  }

  const rec = new SR();
  rec.continuous = false;
  rec.interimResults = false;
  rec.lang = opts.lang || "en-US";

  rec.onresult = (e: any) => {
    try {
      const txt = e?.results?.[0]?.[0]?.transcript;
      if (opts.debug) console.debug("STT result", e);
      if (txt) onText(txt.trim());
    } catch (err) {
      if (opts.debug) console.error("STT result error", err);
    }
  };

  rec.onerror = (err: any) => {
    if (opts.debug) console.error("STT error", err);
  };

  rec.onend = () => {
    if (opts.debug) console.debug("STT ended");
  };

  try {
    rec.start();
    if (opts.debug) console.debug("STT started", { lang: rec.lang });
  } catch (err) {
    if (opts.debug) console.error("STT start failed", err);
  }

  return () => {
    try {
      rec.stop();
      if (opts.debug) console.debug("STT stopped");
    } catch (err) {
      if (opts.debug) console.error("STT stop failed", err);
    }
  };
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
