import { create } from 'zustand'
import axios from 'axios'


interface SettingsStore {
    settingId: string
    locale: string
    timezone: string
    llmProvider: string
    llmApiToken: string
    llmModel: string
    settingsInflight: boolean
    settingsLoaded: boolean

    fetchSettings: () => Promise<void>
    syncSettings: (payload: object)=> Promise<void>
}

// todo axio error handling
// todo jie BE for FE
export const useSettingsStore = create<SettingsStore>()((set, get) => ({
    settingId: "",
    locale: "en-US",
    timezone: "America/Los_Angeles",
    llmProvider: "gemini",
    llmApiToken: "",  // todo/note: token should be encrypted but since it's for local :shrug:
    llmModel: "gemini-2.0-flash",
    settingsInflight: false,
    settingsLoaded: false,

    fetchSettings: () => {
        set({settingsInflight: true})
        return axios.get(`${import.meta.env.VITE_APP_API_BASE_URL}/settings`)
            .then(response => {
                console.log(response)
                set({
                    settingsInflight: false,
                    settingsLoaded: true,
                    settingId: response.data.id,
                    locale: response.data.locale,
                    timezone: response.data.timezone,
                    llmProvider: response.data.llm_provider,
                    llmApiToken: response.data.llm_api_token,
                    llmModel: response.data.llm_model
                })
            })
    },

    syncSettings: async (payload: object) => {
        set({settingsInflight: true})
        const response = await axios.patch(`${import.meta.env.VITE_APP_API_BASE_URL}/settings/${get().settingId}`, payload)
        console.log(response)
        return get().fetchSettings()
    }
}))

export default useSettingsStore