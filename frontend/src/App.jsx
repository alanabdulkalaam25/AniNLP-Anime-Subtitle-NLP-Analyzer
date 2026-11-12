import { useEffect, useRef, useState } from "react";
import { analyzeSubtitle, translateSentences } from "./services/api";

const JLPT_LEVELS = ["N5", "N4", "N3", "N2", "N1", "UNKNOWN"];

const POS_LABELS = {
  ADJECTIVAL_NOUN: "Adjectival noun",
  ADJECTIVE: "Adjective",
  ADVERB: "Adverb",
  AUXILIARY: "Auxiliary",
  CONJUNCTION: "Conjunction",
  INTERJECTION: "Interjection",
  NOUN: "Noun",
  NUMERAL: "Numeral",
  OTHER: "Other",
  PARTICLE: "Particle",
  PREFIX: "Prefix",
  PRENOMINAL: "Pre-nominal",
  PRONOUN: "Pronoun",
  PROPER_NOUN: "Proper noun",
  PUNCTUATION: "Punctuation",
  SUFFIX: "Suffix",
  VERB: "Verb",
};

const SAMPLE_TOKENS = [
  { surface: "アルミン", base: "アルミン", pos: "NOUN", jlpt: "UNKNOWN" },
  { surface: "その", base: "その", pos: "PRENOMINAL", jlpt: "N5" },
  { surface: "日", base: "日", pos: "NOUN", jlpt: "N4" },
  { surface: "人類", base: "人類", pos: "NOUN", jlpt: "N3" },
  { surface: "は", base: "は", pos: "PARTICLE", jlpt: null },
  { surface: "思い出し", base: "思い出す", pos: "VERB", jlpt: "N4" },
  { surface: "た", base: "た", pos: "AUXILIARY", jlpt: null },
];

function formatPos(pos) {
  return (
    POS_LABELS[pos] ??
    pos
      .toLowerCase()
      .replaceAll("_", " ")
      .replace(/^./, (character) => character.toUpperCase())
  );
}

function formatCount(value) {
  return Number(value ?? 0).toLocaleString("en-US");
}

function formatSize(bytes) {
  if (bytes >= 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
  return `${Math.max(1, Math.ceil(bytes / 1024))} KB`;
}

function Icon({ name, size = 16 }) {
  const shapes = {
    chevron: <path d="m9 18 6-6-6-6" />,
    spin: <path d="M21 12a9 9 0 1 1-5.3-8.2" />,
    upload: (
      <>
        <path d="M12 16V4" />
        <path d="m7 9 5-5 5 5" />
        <path d="M5 16v2a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-2" />
      </>
    ),
  };

  return (
    <svg
      aria-hidden="true"
      className={name === "spin" ? "spinner" : undefined}
      fill="none"
      height={size}
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.5"
      viewBox="0 0 24 24"
      width={size}
    >
      {shapes[name]}
    </svg>
  );
}

function CuePreview() {
  return (
    <figure className="cue-preview">
      <div className="cue-preview-head">
        <span className="cue-preview-index">01</span>
        <span className="cue-preview-label">Sample cue</span>
        <span className="cue-preview-time">00:00:26,426 → 00:00:30,263</span>
      </div>
      <p className="cue-preview-text jp">（アルミン）その日 人類は思い出した</p>
      <p className="cue-preview-translation">
        Armin: On that day, humanity remembered.
      </p>
      <div className="cue-preview-tokens">
        {SAMPLE_TOKENS.map((token) => (
          <span className="sample-token" key={`${token.surface}-${token.pos}`}>
            <b className="jp">{token.surface}</b>
            <small>
              {token.base !== token.surface ? `${token.base} · ` : ""}
              {formatPos(token.pos)}
              {token.jlpt ? ` · ${token.jlpt}` : ""}
            </small>
          </span>
        ))}
      </div>
      <figcaption className="cue-preview-foot">
        One cue from the bundled sample · 303 cues in the file
      </figcaption>
    </figure>
  );
}

function StatBand({ analysis }) {
  const stats = analysis.statistics;
  const items = [
    {
      label: "Cues",
      value: formatCount(analysis.subtitle.subtitle_count),
      detail: "timed lines",
    },
    {
      label: "Tokens",
      value: formatCount(stats.total_tokens),
      detail: "morphemes",
    },
    {
      label: "Unique words",
      value: formatCount(stats.unique_words),
      detail: "base forms",
    },
    {
      label: "Avg. per cue",
      value: Number(stats.average_sentence_length).toFixed(2),
      detail: "tokens per cue",
    },
  ];

  return (
    <section className="stat-band" aria-label="Analysis summary">
      {items.map((item) => (
        <div className="stat" key={item.label}>
          <span className="stat-label">{item.label}</span>
          <strong>{item.value}</strong>
          <span className="stat-detail">{item.detail}</span>
        </div>
      ))}
    </section>
  );
}

function JlptSpectrum({ values }) {
  const rows = JLPT_LEVELS.map((level) => ({
    level,
    count: values?.[level] ?? 0,
  }));
  const total = rows.reduce((sum, row) => sum + row.count, 0);
  const matched = rows
    .filter((row) => row.level !== "UNKNOWN")
    .reduce((sum, row) => sum + row.count, 0);
  const summary = rows
    .map((row) => `${row.level} ${row.count}`)
    .join(", ");

  return (
    <section className="panel spectrum-panel">
      <header className="panel-head">
        <div>
          <h2>JLPT reference</h2>
          <p>Community-derived vocabulary labels</p>
        </div>
        <span className="panel-meta">{formatCount(total)} tokens</span>
      </header>

      {total > 0 ? (
        <>
          <div className="spectrum" role="img" aria-label={`JLPT distribution: ${summary}`}>
            {rows
              .filter((row) => row.count > 0)
              .map((row) => (
                <span
                  className={`spectrum-seg level-${row.level}`}
                  key={row.level}
                  style={{ flexGrow: row.count }}
                  title={`${row.level}: ${formatCount(row.count)}`}
                />
              ))}
          </div>
          <div className="spectrum-legend">
            {rows.map((row) => (
              <div className="legend-item" key={row.level}>
                <span
                  aria-hidden="true"
                  className={`legend-dot level-${row.level}`}
                />
                <span className="legend-level">{row.level}</span>
                <span className="legend-count">{formatCount(row.count)}</span>
                <span className="legend-pct">
                  {Math.round((row.count / total) * 100)}%
                </span>
              </div>
            ))}
          </div>
          <p className="panel-foot">
            {formatCount(matched)} tokens matched N5–N1
          </p>
        </>
      ) : (
        <p className="empty">No labelled tokens in this file.</p>
      )}
    </section>
  );
}

function PosLedger({ values }) {
  const rows = Object.entries(values ?? {}).sort(
    ([, aCount], [, bCount]) => bCount - aCount,
  );
  const total = rows.reduce((sum, [, count]) => sum + count, 0);

  return (
    <section className="panel pos-panel">
      <header className="panel-head">
        <div>
          <h2>Parts of speech</h2>
          <p>Every token, tagged</p>
        </div>
        <span className="panel-meta">{formatCount(total)} tokens</span>
      </header>

      {rows.length > 0 ? (
        <div className="pos-ledger">
          {rows.map(([pos, count]) => (
            <div className="pos-row" key={pos}>
              <span className="pos-name">{formatPos(pos)}</span>
              <span className="pos-count">{formatCount(count)}</span>
            </div>
          ))}
        </div>
      ) : (
        <p className="empty">No tokens in this file.</p>
      )}
    </section>
  );
}

function StudyNote({ matched }) {
  return (
    <aside className="study-note">
      <span className="study-note-label">Note</span>
      <p>
        <b>{formatCount(matched)} lexical tokens</b> matched the N5–N1 reference
        data. These are study labels, not an official JLPT assessment.
      </p>
    </aside>
  );
}

function VocabularyTable({ words }) {
  return (
    <section className="panel vocabulary">
      <header className="panel-head">
        <div>
          <h2>Frequent vocabulary</h2>
          <p>Dictionary forms across all cues</p>
        </div>
        <span className="panel-meta">Top {words.length}</span>
      </header>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Word</th>
              <th>Reading</th>
              <th>Part of speech</th>
              <th>JLPT</th>
              <th className="num">Count</th>
            </tr>
          </thead>
          <tbody>
            {words.map((word) => (
              <tr key={`${word.word}-${word.pos}`}>
                <td className="word-cell jp">{word.word}</td>
                <td className="reading-cell">{word.reading ?? "—"}</td>
                <td>{formatPos(word.pos)}</td>
                <td>
                  <span
                    className={`jlpt-tag${
                      word.jlpt && word.jlpt !== "UNKNOWN" ? " is-known" : ""
                    }`}
                  >
                    {word.jlpt ?? "—"}
                  </span>
                </td>
                <td className="num">{formatCount(word.frequency)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function CueSheet({ sentences, translations, translationStatus }) {
  return (
    <section className="panel cue-sheet">
      <header className="panel-head">
        <div>
          <h2>Cue sheet</h2>
          <p>English translation · open a line for tokens</p>
        </div>
        <span className="panel-meta">
          {formatCount(sentences.length)} cues
          {translationStatus === "loading" && " · translating"}
          {translationStatus === "unavailable" && " · no English"}
        </span>
      </header>

      <div className="cue-list">
        {sentences.map((sentence, index) => (
          <details key={`${sentence.index}-${index}`}>
            <summary>
              <span className="cue-chevron" aria-hidden="true">
                <Icon name="chevron" size={16} />
              </span>
              <span className="cue-index">
                {String(sentence.index).padStart(2, "0")}
              </span>
              <span className="cue-copy">
                <span className="cue-text jp">{sentence.text}</span>
                {translations?.[index] && (
                  <span className="cue-translation">
                    {translations[index]}
                  </span>
                )}
              </span>
              <span className="cue-time">
                {sentence.start} → {sentence.end}
              </span>
            </summary>
            <div className="cue-tokens">
              {sentence.tokens.map((token, tokenIndex) => (
                <span
                  className="token"
                  key={`${token.surface}-${tokenIndex}`}
                >
                  <b className="jp">{token.surface}</b>
                  <small>
                    {token.base !== token.surface ? `${token.base} · ` : ""}
                    {formatPos(token.pos)}
                    {token.jlpt ? ` · ${token.jlpt}` : ""}
                  </small>
                </span>
              ))}
            </div>
          </details>
        ))}
      </div>
    </section>
  );
}

export default function App() {
  const fileInput = useRef(null);
  const uploadRef = useRef(null);
  const resultsRef = useRef(null);
  const [file, setFile] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [translations, setTranslations] = useState([]);
  const [translationStatus, setTranslationStatus] = useState("idle");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const prefersReducedMotion = () =>
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  useEffect(() => {
    if (!analysis || !resultsRef.current) return;
    resultsRef.current.scrollIntoView({
      behavior: prefersReducedMotion() ? "auto" : "smooth",
      block: "start",
    });
  }, [analysis]);

  useEffect(() => {
    if (!analysis) {
      setTranslations([]);
      setTranslationStatus("idle");
      return;
    }

    let active = true;
    setTranslations([]);
    setTranslationStatus("loading");

    translateSentences(analysis.sentences.map((sentence) => sentence.text))
      .then((payload) => {
        if (!active) return;
        const values = Array.isArray(payload.translations)
          ? payload.translations
          : [];
        setTranslations(values);
        const allFailed =
          values.length > 0 && payload.failed_count >= values.length;
        setTranslationStatus(allFailed ? "unavailable" : "ready");
      })
      .catch(() => {
        if (!active) return;
        setTranslationStatus("unavailable");
      });

    return () => {
      active = false;
    };
  }, [analysis]);

  async function submit(event) {
    event.preventDefault();

    if (!file) {
      setError("Choose an .srt subtitle file first.");
      fileInput.current?.focus();
      return;
    }

    setError("");
    setIsLoading(true);

    try {
      const result = await analyzeSubtitle(file);
      setAnalysis(result);
    } catch (requestError) {
      setError(requestError.message);
      uploadRef.current?.scrollIntoView({
        behavior: prefersReducedMotion() ? "auto" : "smooth",
        block: "center",
      });
    } finally {
      setIsLoading(false);
    }
  }

  function chooseFile(event) {
    setFile(event.target.files?.[0] ?? null);
    setError("");
  }

  function returnToUpload() {
    uploadRef.current?.scrollIntoView({
      behavior: prefersReducedMotion() ? "auto" : "smooth",
      block: "center",
    });
    fileInput.current?.focus();
  }

  const knownWords = analysis
    ? JLPT_LEVELS.slice(0, 5).reduce(
        (sum, level) => sum + analysis.jlpt_distribution[level],
        0,
      )
    : 0;

  return (
    <div className="app">
      <header className="topbar">
        <div className="shell topbar-inner">
          <div className="brand">
            <span className="brand-seal jp" aria-hidden="true">
              あ
            </span>
            <span className="brand-name">AniNLP</span>
          </div>
          <p className="topbar-line">Japanese subtitle analysis</p>
          <p className="topbar-meta">SRT · 10 MB max</p>
        </div>
      </header>

      <main className="shell">
        <p className="sr-only" role="status">
          {isLoading
            ? "Analyzing subtitle"
            : analysis
              ? translationStatus === "loading"
                ? "Analysis ready. Translating cues."
                : "Analysis ready"
              : ""}
        </p>

        <section className={`masthead${analysis ? " is-compact" : ""}`}>
          <div className="masthead-copy">
            <p className="kicker">Cue-by-cue reading</p>
            <h1>Read the Japanese in your anime, line by line.</h1>
            <p className="lede">
              Upload a subtitle file to see dictionary forms, parts of speech,
              English translations and JLPT reference levels for every cue.
            </p>

            <form
              className="upload-form"
              onSubmit={submit}
              ref={uploadRef}
            >
              <label className="file-picker">
                <input
                  accept=".srt,application/x-subrip"
                  onChange={chooseFile}
                  ref={fileInput}
                  type="file"
                />
                <span className="file-icon" aria-hidden="true">
                  <Icon name="upload" size={16} />
                </span>
                <span className="file-copy">
                  <b>{file ? file.name : "Choose a subtitle file"}</b>
                  <small>
                    {file
                      ? `${formatSize(file.size)} · ready to read`
                      : "Select a Japanese .srt file"}
                  </small>
                </span>
              </label>
              <button type="submit" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Icon name="spin" size={16} />
                    Reading…
                  </>
                ) : (
                  "Analyze"
                )}
              </button>
            </form>

            <p className="upload-note">
              SRT · UTF-8, CP932 or UTF-16 · 10 MB max
            </p>

            {error && (
              <p className="error" role="alert">
                {error}
              </p>
            )}
          </div>

          <CuePreview />
        </section>

        {analysis && (
          <section className="results" ref={resultsRef}>
            <header className="results-head">
              <div>
                <p className="kicker">Analysis</p>
                <h2>{analysis.subtitle.filename}</h2>
                <p className="results-meta">
                  {formatCount(analysis.subtitle.subtitle_count)} cues ·{" "}
                  {formatCount(analysis.statistics.total_tokens)} tokens ·{" "}
                  {formatCount(analysis.statistics.unique_words)} unique words
                </p>
              </div>
              <button
                className="text-action"
                onClick={returnToUpload}
                type="button"
              >
                Analyze another
              </button>
            </header>

            <StatBand analysis={analysis} />

            <div className="analysis-grid">
              <JlptSpectrum values={analysis.jlpt_distribution} />
              <PosLedger values={analysis.pos_distribution} />
            </div>

            <StudyNote matched={knownWords} />

            <VocabularyTable words={analysis.top_words} />

            <CueSheet
              sentences={analysis.sentences}
              translations={translations}
              translationStatus={translationStatus}
            />
          </section>
        )}
      </main>
    </div>
  );
}
