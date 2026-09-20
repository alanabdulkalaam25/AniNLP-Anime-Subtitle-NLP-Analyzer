import { useRef, useState } from "react";
import { analyzeSubtitle } from "./services/api";

const LEVELS = ["N5", "N4", "N3", "N2", "N1", "UNKNOWN"];

function StatCard({ label, value, detail }) {
  return <article className="stat-card"><p>{label}</p><strong>{value}</strong><span>{detail}</span></article>;
}

function Distribution({ title, values, accent = "violet" }) {
  const entries = Object.entries(values ?? {}).filter(([, value]) => value > 0);
  const max = Math.max(...entries.map(([, value]) => value), 1);
  return <section className="panel distribution"><div className="panel-heading"><h2>{title}</h2><span>{entries.reduce((total, [, value]) => total + value, 0)} tokens</span></div>
    {entries.length ? entries.map(([label, value]) => <div className="bar-row" key={label}><span>{label}</span><div className="bar-track"><div className={`bar ${accent}`} style={{ width: `${(value / max) * 100}%` }} /></div><b>{value}</b></div>) : <p className="empty">No matching tokens.</p>}
  </section>;
}

function VocabularyTable({ words }) {
  return <section className="panel vocabulary"><div className="panel-heading"><div><h2>Most frequent vocabulary</h2><p>Dictionary-form lexical words from the subtitle.</p></div><span>Top {words.length}</span></div>
    <div className="table-wrap"><table><thead><tr><th>Word</th><th>Reading</th><th>Part of speech</th><th>JLPT reference</th><th>Frequency</th></tr></thead>
      <tbody>{words.map((word) => <tr key={`${word.word}-${word.pos}`}><td className="japanese">{word.word}</td><td>{word.reading ?? "—"}</td><td>{word.pos}</td><td><span className={`level level-${word.jlpt ?? "none"}`}>{word.jlpt ?? "—"}</span></td><td>{word.frequency}</td></tr>)}</tbody>
    </table></div>
  </section>;
}

function Sentences({ sentences }) {
  return <section className="panel sentences"><div className="panel-heading"><div><h2>Subtitle sentences</h2><p>Inspect the cleaned cue text and its morphological analysis.</p></div><span>{sentences.length} cues</span></div>
    <div className="sentence-list">{sentences.map((sentence) => <details key={sentence.index}><summary><span className="cue-number">{sentence.index}</span><span className="japanese">{sentence.text}</span><time>{sentence.start} → {sentence.end}</time></summary><div className="token-list">{sentence.tokens.map((token, index) => <span className="token" key={`${token.surface}-${index}`}><b>{token.surface}</b><small>{token.base} · {token.pos}{token.jlpt ? ` · ${token.jlpt}` : ""}</small></span>)}</div></details>)}</div>
  </section>;
}

export default function App() {
  const fileInput = useRef(null);
  const [file, setFile] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function submit(event) {
    event.preventDefault();
    if (!file) { setError("Choose an .srt subtitle file first."); return; }
    setError(""); setIsLoading(true);
    try { setAnalysis(await analyzeSubtitle(file)); }
    catch (requestError) { setAnalysis(null); setError(requestError.message); }
    finally { setIsLoading(false); }
  }

  const stats = analysis?.statistics;
  const knownWords = analysis ? LEVELS.slice(0, 5).reduce((sum, level) => sum + analysis.jlpt_distribution[level], 0) : 0;

  return <main>
    <header className="hero"><div className="brand"><span className="brand-mark">あ</span><span>AniNLP</span></div><div className="hero-copy"><p className="eyebrow">Japanese subtitle intelligence</p><h1>Turn anime dialogue into <em>language insight.</em></h1><p className="intro">Upload a Japanese SubRip file to explore vocabulary, morphology, part-of-speech patterns, and community-derived JLPT reference levels.</p></div></header>

    <section className="upload-panel"><div><p className="eyebrow">Analyze a file</p><h2>Your subtitle stays in the analysis flow.</h2><p>Supported: UTF-8 or CP932 encoded <code>.srt</code> files, up to 10 MB.</p></div>
      <form onSubmit={submit}><label className="file-picker"><input ref={fileInput} type="file" accept=".srt,application/x-subrip" onChange={(event) => setFile(event.target.files?.[0] ?? null)} /><span className="file-icon">↑</span><span><b>{file ? file.name : "Choose subtitle file"}</b><small>{file ? `${Math.ceil(file.size / 1024)} KB ready to analyze` : "Select a Japanese .srt file"}</small></span></label><button type="submit" disabled={isLoading}>{isLoading ? "Analyzing…" : "Analyze subtitle"}</button></form>
      {error && <p className="error" role="alert">{error}</p>}
    </section>

    {!analysis && !isLoading && <section className="welcome"><span>✦</span><h2>Your dashboard will appear here.</h2><p>Try the included sample file: <code>sample-data/subtitles/sample.srt</code>.</p></section>}
    {isLoading && <section className="welcome loading"><span>◌</span><h2>Reading the dialogue and mapping its language patterns…</h2></section>}
    {analysis && <section className="results"><div className="result-title"><div><p className="eyebrow">Analysis complete</p><h2>{analysis.subtitle.filename}</h2></div><p>{analysis.subtitle.subtitle_count} subtitle cues analyzed</p></div>
      <div className="stats-grid"><StatCard label="Subtitle cues" value={analysis.subtitle.subtitle_count.toLocaleString()} detail="Timing-preserved entries" /><StatCard label="Tokens" value={stats.total_tokens.toLocaleString()} detail="Morphemes detected" /><StatCard label="Unique words" value={stats.unique_words.toLocaleString()} detail="Lexical base forms" /><StatCard label="Average cue length" value={stats.average_sentence_length} detail="Tokens per cue" /></div>
      <div className="two-column"><Distribution title="JLPT reference distribution" values={analysis.jlpt_distribution} /><Distribution title="Part-of-speech distribution" values={analysis.pos_distribution} accent="teal" /></div>
      <div className="insight"><span>✓</span><p><b>{knownWords} lexical tokens</b> matched the bundled N5–N1 reference dataset. These are learning references, not an official JLPT assessment.</p></div>
      <VocabularyTable words={analysis.top_words} /><Sentences sentences={analysis.sentences} />
    </section>}
  </main>;
}
