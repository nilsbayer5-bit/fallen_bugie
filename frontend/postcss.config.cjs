module.exports = {
  // For local dev we load Tailwind via CDN to avoid PostCSS plugin mismatches.
  // Keep Autoprefixer enabled for basic CSS processing.
  plugins: [
    require('autoprefixer'),
  ],
}
