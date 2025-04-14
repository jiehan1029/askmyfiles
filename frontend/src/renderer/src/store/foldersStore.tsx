import { create } from 'zustand'
import axios from 'axios'

// todo jie: env var
const API_BASE_URL = "http://localhost:8000"


type SyncStatus = {
    folder_path: string
    last_synced_at: string
    total_files: number
    processed_files: number
    status: string
}

type SyncProgress = {
    task_id: string
    directory: string
    status: string
    sync_status_id: string
}

interface FoldersStore {
    syncHistory: Array<SyncStatus>
    syncHistoryInflight: Boolean
    syncHistoryLoaded: Boolean

    fetchSyncHistory: () => Promise<void>
    syncFolders: (folderPath: string)=> Promise<SyncProgress>
}

export const useFoldersStore = create<FoldersStore>()((set, get) => ({
    syncHistory: [],
    syncHistoryInflight: false,
    syncHistoryLoaded: false,

    fetchSyncHistory: () => {
        set({syncHistoryInflight: true})
        return axios.get(`${API_BASE_URL}/synced_folders`)
            .then(response => {
                console.log(response)
                set({
                    syncHistoryInflight: false,
                    syncHistoryLoaded: true,
                    syncHistory: response.data
                })
            })
    },

    syncFolders: (folderPath: string) => {
        return axios.post(`${API_BASE_URL}/insert_documents`, {
                directory: folderPath
            })
            .then(response => {
                console.log(response)
                return response.data
            })
    }
}))

export default useFoldersStore