'use strict';

const fs = require('fs');
const path = require('path');

const theme = require('../src/theme.source.cjs');
const outFile = path.join(__dirname, '..', 'themes', 'hate-of-nature-color-theme.json');

fs.writeFileSync(outFile, `${JSON.stringify(theme, null, 2)}\n`, 'utf8');
console.log(`Built theme: ${outFile}`);
