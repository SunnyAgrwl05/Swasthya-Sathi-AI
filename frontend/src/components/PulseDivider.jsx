export default function PulseDivider() {
  return (
    <svg viewBox="0 0 400 40" className="w-full h-8" preserveAspectRatio="none">
      <line x1="0" y1="20" x2="400" y2="20" stroke="#1B2433" strokeWidth="1" />
      <path
        d="M0 20 H140 L155 6 L170 34 L185 20 H220 L232 12 L244 28 L256 20 H400"
        fill="none"
        stroke="#22E1B2"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray="400"
        className="animate-pulseLine"
        style={{ filter: 'drop-shadow(0 0 6px rgba(34,225,178,0.6))' }}
      />
    </svg>
  )
}
