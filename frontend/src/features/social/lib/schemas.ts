import { z } from 'zod'

export const chatMessageSchema = z.object({
  content: z
    .string()
    .trim()
    .min(1, 'Сообщение не может быть пустым')
    .max(2000, 'Сообщение не должно превышать 2000 символов'),
})

export type ChatMessageFormData = z.infer<typeof chatMessageSchema>
