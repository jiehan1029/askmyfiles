import { create } from 'zustand'
import axios from 'axios'

type ChatRecordType = {
    summary: string | null | undefined
    created_at: number
    conversation_id: string
}

interface ChatHistoryStore {
    chatHistoryInflight: boolean
    chatHistoryLoaded: boolean
    chatHistory: Array<ChatRecordType>

    getChatHistory: () => Promise<void>
    deleteChatHistory: (conversationId: string) => Promise<void>
}

export const useChatHistoryStore = create<ChatHistoryStore>()((set, get) => ({
    chatHistoryInflight: false,
    chatHistoryLoaded: false,
    chatHistory: [],

    getChatHistory: () => {
        set({chatHistoryInflight: true})
        // todo: error handling
        return axios.get(`${import.meta.env.VITE_APP_API_BASE_URL}/chat_history`)
            .then(response=>{
                set({
                    chatHistory: response.data,
                    chatHistoryLoaded: true,
                    chatHistoryInflight: false
                })
            })
    },

    deleteChatHistory: (conversationId: string) => {
        return axios.delete(`${import.meta.env.VITE_APP_API_BASE_URL}/chat_history/${conversationId}`)
            .then(response=>{
                if(response.status === 201){
                    // successfully deleted the conversation, re-fetch the history
                    get().getChatHistory()
                }
                // todo: error handling
            })
    }
}))

export default useChatHistoryStore