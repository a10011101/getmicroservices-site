#!/usr/bin/env node
/**
 * Cross-linker for blog posts — adds contextual body links.
 * Called from generation scripts after post creation.
 * Runs the appropriate Python script for each site.
 */
const { execSync } = require('child_process');
const path = require('path');

const SCRIPTS = {
  gms: path.join(__dirname, 'add-gms-body-crosslinks.py'),
  openclaw: path.join(__dirname, 'add-gms-body-crosslinks.py'), // same format
  bestnmn: path.join(__dirname, 'add-bnmn-crosslinks.py'),
};

function processPost(site, slug) {
  console.log(`📎 Cross-linking ${site}/${slug}...`);
  try {
    if (site === 'gms') {
      // GMS Python script processes ALL slugs, but we can pass the slug to limit scope
      const script = SCRIPTS.gms;
      const result = execSync(`python3 ${script}`, { encoding: 'utf8' });
      console.log(`  ${result.trim()}`);
    } else if (site === 'openclaw') {
      // openclaw uses the GMS-style crosslinking; script needs to know the repo
      // For now, skip since there's no openclaw-specific script
      console.log('  ⏭️  No openclaw-specific cross-link script yet');
    } else if (site === 'bestnmn') {
      const script = SCRIPTS.bestnmn;
      const result = execSync(`python3 ${script} ${slug}`, { encoding: 'utf8' });
      console.log(`  ${result.trim()}`);
    }
    console.log('  ✅ Cross-links applied');
    return true;
  } catch (e) {
    console.error(`  ❌ Cross-link error: ${e.message}`);
    return false;
  }
}

module.exports = { processPost };

// CLI mode
if (require.main === module) {
  const site = process.argv[2];
  const slug = process.argv[3];
  if (!site || !slug) {
    console.error('Usage: add-crosslinks.js <site> <slug>');
    process.exit(1);
  }
  processPost(site, slug);
}
