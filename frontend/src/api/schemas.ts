import { z } from 'zod'
export const sourceCitationSchema = z.object({
  document_id: z.string().min(1), scripture: z.string().min(1),
  chapter: z.number().int().positive(), verse: z.number().int().positive(),
  translation: z.string().default(''), translator: z.string().default(''),
  edition: z.string().default(''), source_reference: z.string().default(''),
  retrieval_score: z.number().min(0).max(1),
})
export const chatResponseSchema = z.object({
  answer: z.string(), grounded: z.boolean(),
  sources: z.array(sourceCitationSchema).default([]),
  message: z.string().nullable().optional(),
})
export const healthResponseSchema = z.object({ status: z.string(), service: z.string() })
export type ValidatedChatResponse = z.infer<typeof chatResponseSchema>
export type ValidatedHealthResponse = z.infer<typeof healthResponseSchema>
