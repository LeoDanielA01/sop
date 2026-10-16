import frappeUIPreset from 'frappe-ui/tailwind'

// Icons typed into resource and record types live in the database, not the source,
// so Tailwind can't see them. Keep a choice of fitting ones in the build.
const RECORD_ICONS = [
  'biohazard', 'boxes', 'box', 'building-2', 'clipboard-list', 'cog', 'door-open', 'droplet', 'ear',
  'factory', 'file-text', 'fire-extinguisher', 'flame', 'flask-conical', 'gauge', 'glasses', 'hammer',
  'hand', 'hard-hat', 'key-round', 'laptop', 'leaf', 'link', 'map-pin', 'package', 'pill', 'radiation',
  'recycle', 'scissors', 'shield-alert', 'shield-check', 'shirt', 'skull', 'sparkles', 'syringe',
  'thermometer', 'trash-2', 'triangle-alert', 'truck', 'users', 'warehouse', 'wrench', 'zap',
]

export default {
  presets: [frappeUIPreset],
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  safelist: RECORD_ICONS.map((name) => `lucide-${name}`),
}
