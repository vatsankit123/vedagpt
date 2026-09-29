/** TypeScript types mirroring VedaGPT FastAPI schemas. Source: backend/app/schemas/chat.py */
export interface ChatRequest { question: string; top_k?: number }
export interface SourceCitation {
  document_id: string; scripture: string; chapter: number; verse: number;
  translation: string; translator: string; edition: string;
  source_reference: string; retrieval_score: number;
}
export interface ChatResponse {
  answer: string; grounded: boolean;
  sources: SourceCitation[]; message: string | null;
}
export interface HealthResponse { status: string; service: string }
