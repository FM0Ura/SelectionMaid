import { describe, expect, it } from 'vitest'
import { MAX_FILE_BYTES, validateFile } from './validators'

function makeFile(type: string, size: number): File {
  const file = new File(['content'], 'document', { type })
  Object.defineProperty(file, 'size', { value: size })
  return file
}

describe('validateFile', () => {
  it('accepts supported files up to 50MB', () => {
    const file = makeFile('application/pdf', MAX_FILE_BYTES)

    expect(validateFile(file)).toBeNull()
  })

  it('rejects files larger than 50MB', () => {
    const file = makeFile('application/pdf', MAX_FILE_BYTES + 1)

    expect(validateFile(file)).toContain('50MB')
  })

  it('rejects unsupported MIME types', () => {
    const file = makeFile('image/png', 100)

    expect(validateFile(file)).toContain('Formato não suportado')
  })

  it.each([
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/html',
  ])('accepts %s', (type) => {
    const file = makeFile(type, 100)

    expect(validateFile(file)).toBeNull()
  })
})
