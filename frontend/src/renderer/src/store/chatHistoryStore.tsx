import { create } from 'zustand'


interface ChatHistoryStore {
    bears: number
    increase: (by: number) => void
}

export const useChatHistoryStore = create<ChatHistoryStore>()((set) => ({
    bears: 0,
    increase: (by) => set((state) => ({ bears: state.bears + by })),
}))

export default useChatHistoryStore