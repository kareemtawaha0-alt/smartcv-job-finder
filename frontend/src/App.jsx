import React, { useState } from "react";
import { uploadCv, analyzeCvText, findJobs } from "./api";

function classNames(...classes) {
  return classes.filter(Boolean).join(" ");
}

export default function App() {
  const [file, setFile] = useState(null);
  const [cvText, setCvText] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [location, setLocation] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [step, setStep] = useState(1);
  const [error, setError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");

  const handleFileChange = (e) => {
    const selected = e.target.files?.[0];
    setFile(selected || null);
    setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setStatusMessage("");

    if (!file) {
      setError("Please select a CV file first.");
      return;
    }

    setIsLoading(true);
    setJobs([]);
    setAnalysis(null);
    setStep(1);

    try {
      setStatusMessage("Uploading CV and extracting text...");
      const uploadResult = await uploadCv(file);
      const extractedText = uploadResult.text;
      setCvText(extractedText);

      setStatusMessage("Analyzing your profile with AI...");
      const analysisResult = await analyzeCvText(extractedText);
      setAnalysis(analysisResult);
      setStep(2);

      setStatusMessage("Searching matching jobs...");
      const jobsResult = await findJobs(analysisResult, location, 20);
      setJobs(jobsResult.jobs || []);
      setStep(3);
      setStatusMessage("");
    } catch (err) {
      console.error(err);
      setError(err.message || "Something went wrong. Please try again.");
      setStatusMessage("");
    } finally {
      setIsLoading(false);
    }
  };

  const hasJobs = jobs && jobs.length > 0;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-5xl space-y-8">
        <header className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl sm:text-4xl font-semibold bg-gradient-to-r from-sky-400 to-blue-500 bg-clip-text text-transparent">
              SmartCV Job Finder
            </h1>
            <p className="text-slate-400 mt-1">
              Upload your CV, let AI analyze your profile, and get job matches
              in seconds.
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs sm:text-sm text-slate-400">
            <span className="inline-flex h-2 w-2 rounded-full bg-emerald-400 mr-1" />
            <span>Secure &amp; read-only · We never auto-apply</span>
          </div>
        </header>

        <main className="grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1.8fr)]">
          {/* LEFT: Controls & Status */}
          <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 sm:p-6 shadow-lg shadow-slate-950/40 space-y-6">
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-slate-400">
                <span className="h-px flex-1 bg-slate-700" />
                <span>Start here</span>
                <span className="h-px flex-1 bg-slate-700" />
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-200 mb-1.5">
                    CV / Resume file
                  </label>
                  <label
                    htmlFor="cv-file"
                    className={classNames(
                      "flex items-center justify-between gap-3 rounded-xl border border-dashed px-3 py-2.5 cursor-pointer transition",
                      file
                        ? "border-emerald-500/70 bg-emerald-500/5 hover:bg-emerald-500/10"
                        : "border-slate-700 hover:border-slate-500 hover:bg-slate-800/40"
                    )}
                  >
                    <div className="flex flex-col">
                      <span className="text-xs font-medium text-slate-200">
                        {file ? file.name : "Choose a PDF or DOCX file"}
                      </span>
                      <span className="text-[11px] text-slate-500">
                        Max ~10MB. We only read text and never auto-apply.
                      </span>
                    </div>
                    <span className="text-xs font-semibold text-sky-300">
                      Browse
                    </span>
                  </label>
                  <input
                    id="cv-file"
                    type="file"
                    accept=".pdf,.docx,.txt"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-200 mb-1.5">
                    Preferred location (optional)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Remote, Dubai, London..."
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-900/70 px-3 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500/70 focus:border-sky-500"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isLoading || !file}
                  className={classNames(
                    "w-full inline-flex items-center justify-center gap-2 rounded-xl px-3 py-2.5 text-sm font-medium transition",
                    isLoading || !file
                      ? "bg-slate-700 text-slate-400 cursor-not-allowed"
                      : "bg-gradient-to-r from-sky-500 to-blue-600 text-white shadow-md shadow-sky-900/40 hover:from-sky-400 hover:to-blue-500"
                  )}
                >
                  {isLoading ? (
                    <>
                      <span className="h-4 w-4 border-2 border-slate-300/60 border-t-transparent rounded-full animate-spin" />
                      <span>Working on it...</span>
                    </>
                  ) : (
                    <>
                      <span>Find matching jobs</span>
                    </>
                  )}
                </button>
              </form>
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex items-center gap-2 text-slate-300 font-medium">
                <span>Status</span>
                {statusMessage && (
                  <span className="h-1.5 w-1.5 rounded-full bg-sky-400 animate-pulse" />
                )}
              </div>
              <div className="min-h-[2.5rem] rounded-xl border border-slate-800 bg-slate-900/40 px-3 py-2 flex items-center text-[11px] text-slate-400">
                {statusMessage
                  ? statusMessage
                  : "Ready when you are. Upload your CV and we’ll guide you through each step."}
              </div>

              <div className="grid grid-cols-3 gap-1.5 text-[11px]">
                <StepPill label="Upload CV" index={1} activeStep={step} />
                <StepPill label="AI Analysis" index={2} activeStep={step} />
                <StepPill label="Job Matches" index={3} activeStep={step} />
              </div>
            </div>

            {error && (
              <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 text-rose-100 text-xs px-3 py-2">
                {error}
              </div>
            )}

            {analysis && (
              <div className="mt-1 space-y-3 text-xs">
                <h2 className="text-sm font-semibold text-slate-100">
                  AI profile snapshot
                </h2>
                {analysis.summary && (
                  <p className="text-slate-400 leading-relaxed">
                    {analysis.summary}
                  </p>
                )}
                <div className="flex flex-wrap gap-2">
                  {analysis.job_titles?.slice(0, 4).map((t) => (
                    <span
                      key={t}
                      className="px-2 py-1 rounded-full bg-sky-500/10 border border-sky-500/40 text-[11px] text-sky-100"
                    >
                      {t}
                    </span>
                  ))}
                  {analysis.recommended_job_types?.slice(0, 4).map((t) => (
                    <span
                      key={t}
                      className="px-2 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/40 text-[11px] text-emerald-100"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </section>

          {/* RIGHT: Results table */}
          <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 sm:p-6 shadow-lg shadow-slate-950/40 flex flex-col">
            <div className="flex items-center justify-between gap-3 mb-4">
              <div>
                <h2 className="text-lg sm:text-xl font-semibold text-slate-50">
                  Matching jobs
                </h2>
                <p className="text-xs text-slate-500">
                  We never auto-apply. Click a row to open the job listing in a
                  new tab.
                </p>
              </div>
              {hasJobs && (
                <div className="text-[11px] text-slate-400">
                  Found{" "}
                  <span className="font-semibold text-sky-300">
                    {jobs.length}
                  </span>{" "}
                  jobs
                </div>
              )}
            </div>

            <div className="flex-1 rounded-xl border border-slate-800 bg-slate-950/40 overflow-hidden">
              {isLoading && (
                <div className="flex flex-col items-center justify-center h-64 gap-3">
                  <span className="h-8 w-8 border-2 border-slate-300/70 border-t-transparent rounded-full animate-spin" />
                  <p className="text-xs text-slate-400">
                    Finding the best job matches for your profile...
                  </p>
                </div>
              )}

              {!isLoading && !hasJobs && (
                <div className="flex flex-col items-center justify-center h-64 gap-3 text-center px-4">
                  <p className="text-sm text-slate-300 font-medium">
                    No jobs to show yet.
                  </p>
                  <p className="text-xs text-slate-500 max-w-sm">
                    Upload your CV and we&apos;ll analyze your skills and
                    recommend jobs tailored to your profile.
                  </p>
                </div>
              )}

              {!isLoading && hasJobs && (
                <div className="overflow-auto max-h-[480px]">
                  <table className="min-w-full text-left text-xs">
                    <thead className="sticky top-0 z-10 bg-slate-900/95 backdrop-blur border-b border-slate-800">
                      <tr>
                        <th className="px-3 py-2.5 font-semibold text-slate-300 w-1/3">
                          Job title
                        </th>
                        <th className="px-3 py-2.5 font-semibold text-slate-300 w-1/5">
                          Company
                        </th>
                        <th className="px-3 py-2.5 font-semibold text-slate-300 w-1/6">
                          Location
                        </th>
                        <th className="px-3 py-2.5 font-semibold text-slate-300">
                          Description
                        </th>
                        <th className="px-3 py-2.5 font-semibold text-slate-300 text-right">
                          Apply
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/80">
                      {jobs.map((job, idx) => (
                        <tr
                          key={`${job.apply_link}-${idx}`}
                          className="hover:bg-slate-900/80 cursor-pointer transition"
                          onClick={() => {
                            if (job.apply_link) {
                              window.open(job.apply_link, "_blank", "noopener");
                            }
                          }}
                        >
                          <td className="px-3 py-2.5 align-top">
                            <div className="flex flex-col gap-0.5">
                              <span className="font-medium text-slate-100">
                                {job.title}
                              </span>
                              {job.source && (
                                <span className="text-[10px] uppercase tracking-wide text-slate-500">
                                  {job.source}
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="px-3 py-2.5 align-top text-slate-200">
                            {job.company}
                          </td>
                          <td className="px-3 py-2.5 align-top text-slate-300">
                            {job.location}
                          </td>
                          <td className="px-3 py-2.5 align-top text-slate-400">
                            <p className="line-clamp-3">
                              {job.description || "No description provided."}
                            </p>
                          </td>
                          <td className="px-3 py-2.5 align-top text-right">
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                if (job.apply_link) {
                                  window.open(
                                    job.apply_link,
                                    "_blank",
                                    "noopener"
                                  );
                                }
                              }}
                              className="inline-flex items-center justify-center px-2.5 py-1.5 rounded-full text-[11px] font-medium bg-sky-500/90 hover:bg-sky-400 text-white shadow-md shadow-sky-900/40"
                            >
                              Open link
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </section>
        </main>

        <footer className="text-[11px] text-slate-500 text-center">
          Built for demo purposes. Make sure to review each job listing before
          applying. We never store or share your data by default.
        </footer>
      </div>
    </div>
  );
}

function StepPill({ label, index, activeStep }) {
  const isActive = activeStep === index;
  const isCompleted = activeStep > index;

  return (
    <div
      className={classNames(
        "flex items-center justify-center gap-1 px-2 py-1 rounded-full border text-[11px]",
        isCompleted
          ? "border-emerald-500/60 bg-emerald-500/10 text-emerald-100"
          : isActive
          ? "border-sky-500/70 bg-sky-500/10 text-sky-100"
          : "border-slate-700 bg-slate-900/60 text-slate-400"
      )}
    >
      <span
        className={classNames(
          "h-1.5 w-1.5 rounded-full",
          isCompleted
            ? "bg-emerald-400"
            : isActive
            ? "bg-sky-400"
            : "bg-slate-600"
        )}
      />
      <span>{label}</span>
    </div>
  );
}
