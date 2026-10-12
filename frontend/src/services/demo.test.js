import assert from 'node:assert/strict';
import test from 'node:test';

import { getPublicDemoUrl } from './demo.js';

test('accepts a separate HTTPS demo deployment', () => {
  assert.equal(
    getPublicDemoUrl('https://demo.resq.example/', 'https://resq.example'),
    'https://demo.resq.example/',
  );
});

test('hides the demo link when unset, insecure, credentialed, or same-origin', () => {
  assert.equal(getPublicDemoUrl('', 'https://resq.example'), '');
  assert.equal(getPublicDemoUrl('http://demo.resq.example/', 'https://resq.example'), '');
  assert.equal(getPublicDemoUrl('https://user:pass@demo.resq.example/', 'https://resq.example'), '');
  assert.equal(getPublicDemoUrl('https://resq.example/demo', 'https://resq.example'), '');
});
