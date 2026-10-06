// Node build step: minifies src/ (HTML, CSS, JS) into static/, which Flask serves.
const esbuild = require('esbuild');
const fs = require('fs');
const watch = process.argv.includes('--watch');
const opts = { entryPoints: ['src/app.js', 'src/style.css'], outdir: 'static', bundle: true, minify: true, logLevel: 'info' };
const copyHtml = () => { fs.mkdirSync('static', { recursive: true }); fs.copyFileSync('src/index.html', 'static/index.html'); };
(async () => {
  copyHtml();
  if (watch) {
    const ctx = await esbuild.context(opts); await ctx.watch();
    fs.watch('src/index.html', copyHtml); console.log('Watching src/ …');
  } else { await esbuild.build(opts); console.log('Frontend built into static/'); }
})();
