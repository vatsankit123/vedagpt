import type { ChatResponse, HealthResponse, SourceCitation } from '@/api/types'
export const mockSource: SourceCitation = {
  document_id: 'gita-2-47', scripture: 'Bhagavad Gita', chapter: 2, verse: 47,
  translation: 'DEMO: You have a right to perform your prescribed duties, but not to the fruits of your actions.',
  translator: 'Fixture Translator', edition: 'Fixture Edition 1.0',
  source_reference: 'https://fixture.example.com/gita/2/47', retrieval_score: 0.87,
}
export const mockSource2: SourceCitation = {
  document_id: 'gita-2-48', scripture: 'Bhagavad Gita', chapter: 2, verse: 48,
  translation: 'DEMO: Perform your duty equipoised, abandoning all attachment.',
  translator: 'Fixture Translator', edition: 'Fixture Edition 1.0',
  source_reference: 'https://fixture.example.com/gita/2/48', retrieval_score: 0.72,
}
export const mockGroundedResponse: ChatResponse = {
  answer: 'DEMO: According to the indexed passages, performing duty without attachment is a core teaching.',
  grounded: true, sources: [mockSource], message: null,
}
export const mockGroundedMultiSource: ChatResponse = {
  answer: 'DEMO: Multiple passages discuss performing duty.', grounded: true, sources: [mockSource, mockSource2], message: null,
}
export const mockUngroundedResponse: ChatResponse = {
  answer: 'I could not find sufficient support for this question in the currently indexed sources.',
  grounded: false, sources: [], message: 'Insufficient evidence in the indexed corpus.',
}
export const mockHealthOk: HealthResponse = { status: 'ok', service: 'vedagpt-api' }
