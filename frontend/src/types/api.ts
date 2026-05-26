export interface Chunk {
  chunk_id: string
  content: string
  page_start: number
  page_end: number
  section_title: string
  chunk_index: number
  total_chunks: number
  word_count: number
}

export interface DocumentMetadata {
  doc_id: string
  source_filename: string
  title: string
  author: string
  language: string
  doc_type: string
  page_count: number
  chunk_count: number
  ingested_at: string
}

export interface ExtractionResponse {
  metadata: DocumentMetadata
  chunks: Chunk[]
}

export type UploadStatus =
  | 'idle'
  | 'dragging'
  | 'uploading'
  | 'processing'
  | 'success'
  | 'error'

export type UploadState =
  | { status: 'idle' }
  | { status: 'dragging' }
  | { status: 'uploading'; progress: number }
  | { status: 'processing' }
  | { status: 'success'; data: ExtractionResponse }
  | { status: 'error'; message: string; code?: string }
