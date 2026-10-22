import { createContext, useContext } from 'react'
import { useChatSocket } from './useChatSocket'

const ChatSocketContext = createContext<React.RefObject<WebSocket | null> | null>(null)

export function ChatSocketProvider({ children }: { children: React.ReactNode }) {
  const socketRef = useChatSocket()
  return <ChatSocketContext.Provider value={socketRef}>{children}</ChatSocketContext.Provider>
}

export function useChatSocketRef() {
  const ctx = useContext(ChatSocketContext)
  if (!ctx) throw new Error('useChatSocketRef must be used inside ChatSocketProvider')
  return ctx
}
