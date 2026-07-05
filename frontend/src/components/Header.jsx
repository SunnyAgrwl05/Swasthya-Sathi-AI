import PulseDivider from "./PulseDivider";
import biharHealth from "../assets/bihar-health.png";

export default function Header() {
  return (
    <header className="mb-8 px-1">     <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-5">

      {/* Left Section */}
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-pulse to-pulse2 flex items-center justify-center shadow-[0_0_25px_rgba(45,212,191,0.45)] animate-floatY">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
            <path
              d="M3 12h4l2-7 4 14 2-7h6"
              stroke="#080B10"
              strokeWidth="2.3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>

        <div>
          <h1 className="font-display text-2xl sm:text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white via-cyan-200 to-teal-300 bg-clip-text text-transparent drop-shadow-[0_0_14px_rgba(34,211,238,0.45)]"> Swasthya Sathi AI
          </h1>

          <p className="mt-1 text-xs sm:text-sm font-medium tracking-wide text-cyan-200/90 max-w-lg">
            AI Workforce Intelligence for Bihar Health Department
          </p>
        </div>
      </div>

      {/* Right Badge */}
      <div className="self-start lg:self-auto flex items-center gap-2 px-4 py-2 rounded-full border border-cyan-400/40 bg-gradient-to-r from-cyan-500/10 to-teal-500/10 shadow-[0_0_22px_rgba(34,211,238,0.25)] backdrop-blur-md">
        <img
          src={biharHealth}
          alt="Bihar Health Department"
          className="w-6 h-6 rounded-full object-cover"
        />

        <span className="text-sm font-semibold tracking-wide text-cyan-100">
          🤖 AI Powered • Bihar Health Dept.
        </span>
      </div>

    </div>

      <div className="mt-4">
        <PulseDivider />
      </div>
    </header>
  );
}

