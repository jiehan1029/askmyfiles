import { create } from 'zustand'


type messageListType = {
    from: "AI" | "US",
    text: string
}


interface ChatStore {
    conversationId: string | null | undefined
    messageList: Array<messageListType>
    
    addMessageToList: (message: string, from: "AI" | "US") => void
    startNewConversation: () => void
}

export const useChatStore = create<ChatStore>()((set, get) => ({
    conversationId: null,
    messageList: [],

    addMessageToList: (message: string, from: "AI" | "US")=>{
        const newMessage: messageListType = {
            from,
            text: message
        }
        const newMsgList = get().messageList.concat([newMessage])
        set({ messageList: newMsgList })
    },

    startNewConversation: () => {
        set({conversationId: null, messageList: []})
    }
}))

export default useChatStore