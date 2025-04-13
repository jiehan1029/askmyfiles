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

interface FoldersStore {
    syncHistory: Array<SyncStatus>
    syncHistoryInflight: Boolean
    syncHistoryLoaded: Boolean

    fetchSyncHistory: () => void
}

export const useFoldersStore = create<FoldersStore>()((set, get) => ({
    syncHistory: [],
    syncHistoryInflight: false,
    syncHistoryLoaded: false,

    fetchSyncHistory: () => {
        set({syncHistoryInflight: true})
        console.log('***** inside fetch,', get().syncHistoryLoaded)
        axios.get(`${API_BASE_URL}/synced_folders`)
            .then(response => {
                console.log(response)
                set({
                    syncHistoryInflight: false,
                    syncHistoryLoaded: true,
                    syncHistory: response.data
                })
            })
    },
}))

export default useFoldersStore