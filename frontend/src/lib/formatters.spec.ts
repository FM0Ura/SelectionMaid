import { describe, expect, it } from 'vitest'
import { formatDate, formatDuration, formatFileSize, formatPageRange, slugifyFilename } from './formatters'

describe('formatFileSize', () => {
  it('formats bytes using human-readable units', () => {
    expect(formatFileSize(0)).toBe('0 B')
    expect(formatFileSize(1024)).toBe('1.0 KB')
    expect(formatFileSize(1048576)).toBe('1.0 MB')
  })
})

describe('formatDuration', () => {
  it('formats durations below and above one second', () => {
    expect(formatDuration(0)).toBe('< 1s')
    expect(formatDuration(0.5)).toBe('< 1s')
    expect(formatDuration(1.5)).toBe('1.5s')
  })
})

describe('formatDate', () => {
  it('formats ISO dates in compact pt-BR date and time style', () => {
    expect(formatDate('2026-05-26T15:30:00.000Z')).toMatch(/26\/05\/26,? 12:30/)
  })
})

describe('formatPageRange', () => {
  it('formats single pages and page intervals', () => {
    expect(formatPageRange(2, 2)).toBe('Pg 2')
    expect(formatPageRange(1, 3)).toBe('Pgs 1-3')
  })
})

describe('slugifyFilename', () => {
  it('strips extension and slugifies ASCII filenames', () => {
    expect(slugifyFilename('report.pdf')).toBe('report')
  })
  it('strips Portuguese diacritics', () => {
    expect(slugifyFilename('Calendário de Provas 2026.pdf')).toBe('calendario-de-provas-2026')
  })
  it('collapses multiple non-alphanumeric chars into a single hyphen', () => {
    expect(slugifyFilename('my  file--name.docx')).toBe('my-file-name')
  })
  it('trims leading and trailing hyphens', () => {
    expect(slugifyFilename('-bad-name-.pdf')).toBe('bad-name')
  })
})
