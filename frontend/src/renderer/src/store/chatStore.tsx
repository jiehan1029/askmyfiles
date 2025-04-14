import { create } from 'zustand'
import { toast } from "sonner"


type messageListType = {
    from: "AI" | "US",
    text: string
}

interface ChatStore {
    conversationId: string | null | undefined
    messageList: Array<messageListType>
    messageInflight: boolean

    socket: WebSocket | null
    socketIsConnected: boolean
    socketError: boolean

    addMessageToList: (message: string, from: "AI" | "US") => void
    startNewConversation: () => void

    connectSocket: () => void
    disconnectSocket: () => void
    sendMessage: (message: string) => void
}

export const useChatStore = create<ChatStore>()((set, get) => ({
    conversationId: null,
    messageList: [],
    messageInflight: false,
    socket: null,
    socketIsConnected: false,
    socketError: false,


    addMessageToList: (message: string, from: "AI" | "US")=>{
        const newMessage: messageListType = {
            from,
            text: message
        }
        const newMsgList = get().messageList.concat([newMessage])
        set({ messageList: newMsgList })
    },

    startNewConversation: () => {
        set({
            conversationId: null,
            messageList: [],
            messageInflight: false
        })
    },

    connectSocket: () => {
        const wsUrl = `${import.meta.env.VITE_APP_WS_BASE_URL}/ws/chat`
        const socket = new WebSocket(wsUrl)
        socket.onopen = () => {
            toast("Start your chat with AI assistant!")
            console.log("WebSocket connected")
            set({ socket, socketIsConnected: true, socketError: false, messageInflight: false })
        }

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data)
            console.log("WS message:", data)

            if(data.status === "complete"){
                set({messageInflight: false})
                get().addMessageToList(data.answer, "AI")
            }else if(data.status === "error"){
                set({messageInflight: false})
                get().addMessageToList(data.error, "AI")
            }
            // note: UI implemented loading separately, don't need to display "thinking" from backend
        }

        socket.onerror = (e) => {
            console.error("WebSocket error:", e)
            set({
                socketError: true,
                socketIsConnected: false,
                messageInflight: false
            })
            toast("Error connecting to the server.")
        }

        socket.onclose = (e) => {
            console.log("WebSocket closed:", e.code, e.reason)
            set({ socketIsConnected: false, socket: null, socketError: false, messageInflight: false })
        }
    },

    disconnectSocket: () => {
        get().socket?.close()
        set({ socket: null, socketIsConnected: false, socketError: false, messageInflight: false })
    },

    sendMessage: (message: string) => {
        set({messageInflight: true})
        const { socket, conversationId } = get()
        if (socket && socket.readyState === WebSocket.OPEN) {
            const payload: any = {
                question: message,
                history_limit: 10
            }
            if (conversationId) {
                payload.conversation_id = conversationId
            }

            socket.send(JSON.stringify(payload))
            get().addMessageToList(message, "US")
        } else {
            console.warn("WebSocket not ready")
            set({messageInflight: false})
            // todo: error handling / settimeout until socket ready
        }
    }
}))

export default useChatStore