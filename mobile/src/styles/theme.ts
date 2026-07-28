/**
 * Lumine Design System — Full Light Theme.
 * Single source of truth for all screens.
 * Dark theme retired. Do not re-introduce dark values.
 */

export const THEME = {
  colors: {
    background: '#FAF7F2',    // screen background — warm off-white
    card: '#FFFFFF',          // card / panel surface
    input: '#F5F2EC',         // text input background
    surface: '#F5F2EC',       // secondary surface — chips, inactive buttons
    divider: '#F0EBE3',       // horizontal rules, separators

    primary: '#C9974A',       // gold — CTA buttons, accents, links, sparkle
    primaryShadow: '#C9974A', // card shadow tint (shadowColor)

    text: '#1A1A1A',          // primary text — headings, input values
    textSecondary: '#9A9A9A', // secondary text — subtitles, labels, icons
    textMuted: '#B0A898',     // placeholder text, disabled/hint text
    soldBy: '#9A9A9A',        // "Sold by:" label on task cards

    error: '#DC2626',         // validation errors, destructive actions
    success: '#16a34a',       // success states, Done status badge
    warning: '#d97706',       // Pending badge, upload warnings

    // Status badge colours — openapi.yaml FollowUpTask.status enum
    statusPending: '#d97706',
    statusDone: '#16a34a',
    statusSuperseded: '#9A9A9A',

    // Upload log status badge colours — openapi.yaml UploadLog.status enum
    uploadSuccess: '#16a34a',
    uploadSuccessBg: '#dcfce7',
    uploadError: '#DC2626',
    uploadErrorBg: '#fee2e2',

    overlay: 'rgba(0,0,0,0.4)', // modal/drawer backdrop scrim
  },

  /**
   * Spacing scale — padding, margin, gap.
   */
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
  },

  /**
   * Border radius scale.
   * sm=8  — small buttons, badge corners
   * md=12 — input rows, cards
   * lg=20 — modal cards, large panels
   * pill=50 — CTA buttons (Login / Register)
   */
  radius: {
    sm: 8,
    md: 12,
    lg: 20,
    pill: 50,
  },

  /**
   * Font size scale.
   */
  fontSize: {
    xs: 11,    // badge text
    sm: 13,    // captions, error text, subtitles, sold-by
    md: 15,    // body text, input text
    lg: 16,    // button text, section body
    xl: 18,    // card titles
    xxl: 24,   // screen titles
    brand: 32, // LUMINE wordmark
  },
} as const;

export type Theme = typeof THEME;
