export const isMessagesQuery = (q: { queryKey: readonly unknown[] }) =>
  typeof q.queryKey[0] === 'string' && q.queryKey[0].startsWith('/api/v1/social/messages')
