import { create } from 'zustand'
import axios from 'axios'


type SyncStatus = {
    folder_path: string
    last_synced_at: number
    total_files: number
    processed_files: number
    skipped_files: number
    status: string
}

type SyncProgress = {
    task_id: string
    directory: string
    status: string
    sync_status_id: string
}

interface FoldersStore {
    numFilesSynced: number
    syncHistory: Array<SyncStatus>
    syncHistoryInflight: Boolean
    syncHistoryLoaded: Boolean

    fetchSyncHistory: () => Promise<void>
    syncFolders: (folderPath: string)=> Promise<SyncProgress>
    deleteFolder: (folderPath: string)=> Promise<void>
}

export const useFoldersStore = create<FoldersStore>()((set, get) => ({
    numFilesSynced: 0,
    syncHistory: [],
    syncHistoryInflight: false,
    syncHistoryLoaded: false,

    fetchSyncHistory: () => {
        set({syncHistoryInflight: true})
        return axios.get(`${import.meta.env.VITE_APP_API_BASE_URL}/synced_folders`)
            .then(response => {
                set({
                    syncHistoryInflight: false,
                    syncHistoryLoaded: true,
                    syncHistory: response.data.results,
                    numFilesSynced: response.data.file_count
                })
            })
    },

    syncFolders: async (folderPath: string) => {
        const homeDir = await window.api.getHomeDir()
        const response = await axios.post(`${import.meta.env.VITE_APP_API_BASE_URL}/insert_documents`, {
                directory: folderPath,
                home_dir: homeDir
            })
        return response.data
    },

    deleteFolder: async (folderPath: string) => {
        const homeDir = await window.api.getHomeDir()
        return axios.post(`${import.meta.env.VITE_APP_API_BASE_URL}/delete_folder`, {
            directory: folderPath,
            home_dir: homeDir
        }).then(response =>{
            if(response.status === 201){
                get().fetchSyncHistory()
            }
        })
    }
}))

export default useFoldersStore