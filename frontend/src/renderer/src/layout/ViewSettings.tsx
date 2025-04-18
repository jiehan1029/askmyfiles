import { Separator } from "@renderer/shared/components/ui/separator"
import { Select,
    SelectContent,
    SelectGroup,
    SelectItem,
    SelectLabel,
    SelectTrigger,
    SelectValue,
} from "@renderer/shared/components/ui/select"
import { Button } from "@renderer/shared/components/ui/button"
import { Input } from "@renderer/shared/components/ui/input"
import { useEffect, useState } from "react"
import localeCodes from "locale-codes"
import useSettingsStore from "@renderer/store/settingsStore"
import { Skeleton } from "@renderer/shared/components/ui/skeleton"


const DEFAULT_MODEL_MAP = {
    gemini: "gemini-2.0-flash",
    huggingFace: "HuggingFaceH4/zephyr-7b-beta",
    ollama: "mistral:7b"
}

export function SettingsView() {
    const [tokenInputDisabled, setTokenInputDisabled] = useState<boolean>(false)
    const [provider, setProvider] = useState<string>("gemini")
    const [apiToken, setApiToken] = useState<string>("")
    const [model, setModel] = useState<string>("")
    const [locale, setLocale] = useState<string>("en-US")
    const [timezone, setTimezone] = useState<string>("America/Los_Angeles")

    const allLocales = localeCodes.all.map((entry) => entry.tag) // BCP 47 tags like "en", "fr-CA"
    const allTimezones = Intl.supportedValuesOf('timeZone')

    const settingsStore = useSettingsStore()

    const resetSettings = ()=>{
        setProvider(settingsStore.llmProvider)
        setApiToken(settingsStore.llmApiToken)
        setModel(settingsStore.llmModel)
        setLocale(settingsStore.locale)
        setTimezone(settingsStore.timezone)
    }

    useEffect(()=>{
        if(!settingsStore.settingsLoaded){
            settingsStore.fetchSettings().then(()=>{
                resetSettings()
            })
        } else {
            resetSettings()
        }
    }, [])

    const onSelectProvider = (newVal) => {
        if(newVal !== provider){
            setProvider(newVal)
            setApiToken("")
            setModel(DEFAULT_MODEL_MAP[newVal])
            if(newVal !== "ollama"){
                setTokenInputDisabled(false)
            } else {
                setTokenInputDisabled(true)
            }
        }
        
    }

    const onChangeApiToken = (evt) => {
        setApiToken(evt.target.value)
    }

    const onChangeModel = (evt) => {
        setModel(evt.target.value)
    }

    const onSelectLocale = (newVal) => {
        setLocale(newVal)
    }

    const onSelectTimezone = (newVal) => {
        setTimezone(newVal)
    }

    const onClickSaveSettings = () => {
        settingsStore.syncSettings({
            locale: locale,
            timezone: timezone,
            llm_provider: provider,
            llm_api_token: apiToken,
            llm_model: model
        })
    }

    return <>
        <div className="p-2 pb-12 overflow-scroll">
            {!settingsStore.settingsLoaded && (<>
                <div style={{ marginTop: '12px'}}>
                    <Skeleton className="h-4 w-[calc(100%-32px)]" style={{ marginBottom: '8px'}} />
                    <Skeleton className="h-4 w-[calc(60%)]" />
                </div>
                <div style={{ marginTop: '12px'}}>
                    <Skeleton className="h-4 w-[calc(100%-32px)]" style={{ marginBottom: '8px'}} />
                    <Skeleton className="h-4 w-[calc(60%)]" />
                </div>
                <div style={{ marginTop: '12px'}}>
                    <Skeleton className="h-4 w-[calc(100%-32px)]" style={{ marginBottom: '8px'}} />
                    <Skeleton className="h-4 w-[calc(60%)]" />
                </div>
                <div style={{ marginTop: '12px'}}>
                    <Skeleton className="h-4 w-[calc(100%-32px)]" style={{ marginBottom: '8px'}} />
                    <Skeleton className="h-4 w-[calc(60%)]" />
                </div>
            </>)}
            {settingsStore.settingsLoaded && (<>
            <section>
                <h3 className="text-lg" style={{fontWeight: 600}}>LLM Provider Settings</h3>
                <sub>
                Select an LLM provider and enter your API token to enable answer generation.
                <br />
                If you're using Ollama, the API token is not required — just make sure the model is configured in the Ollama dashboard.
                </sub>
                <div className="flex flex-row items-center justify-start" style={{ marginBottom: '12px', marginTop: '12px'}}>
                    <div className="w-[100px]">Provider</div>
                    <Select value={provider} onValueChange={onSelectProvider}>
                        <SelectTrigger className="w-[180px]">
                            <SelectValue placeholder="Select a provider" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectGroup>
                            <SelectLabel>Providers</SelectLabel>
                            <SelectItem value="gemini">Gemini</SelectItem>
                            <SelectItem value="huggingFace">Hugging Face</SelectItem>
                            <SelectItem value="ollama">Ollama</SelectItem>
                            </SelectGroup>
                        </SelectContent>
                    </Select>
                </div>
                <div className="flex flex-row items-center justify-start" style={{ marginBottom: '12px'}}>
                    <div className="w-[100px]">API Token</div>
                    <Input type="text" value={apiToken} disabled={tokenInputDisabled} className="w-[280px]" onChange={onChangeApiToken}/>
                </div>
                <div className="flex flex-row items-center justify-start" style={{ marginBottom: '12px'}}>
                    <div className="w-[100px]">Model</div>
                    <Input type="text" value={model} className="w-[280px]" onChange={onChangeModel}/>
                </div>
            </section>
            <Separator style={{margin: '12px 0'}}/>
            <section>
                <h3 className="text-lg" style={{fontWeight: 600}}>Timezone Settings</h3>
                <sub>Set which locale and timezone you'd like to display your datetime.</sub>
                <div className="flex flex-row items-center justify-start" style={{ marginBottom: '12px', marginTop: '12px'}}>
                    <div className="w-[100px]">Locale</div>
                    <Select value={locale} onValueChange={onSelectLocale}>
                        <SelectTrigger className="w-[280px]">
                            <SelectValue placeholder="Select your locale" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectGroup>
                            <SelectLabel>Locales</SelectLabel>
                            {allLocales.map((locale) => (
                            <SelectItem key={locale} value={locale}>{locale}</SelectItem>
                            ))}
                            </SelectGroup>
                        </SelectContent>
                    </Select>
                </div>
                <div className="flex flex-row items-center justify-start" style={{ marginBottom: '12px', marginTop: '12px'}}>
                    <div className="w-[100px]">Timezone</div>
                    <Select value={timezone} onValueChange={onSelectTimezone}>
                        <SelectTrigger className="w-[280px]">
                            <SelectValue placeholder="Select your timezone" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectGroup>
                            <SelectLabel>Timezones</SelectLabel>
                            {allTimezones.map((tz) => (
                            <SelectItem key={tz} value={tz}>{tz}</SelectItem>
                            ))}
                            </SelectGroup>
                        </SelectContent>
                    </Select>
                </div>
            </section>
            <Separator style={{margin: '12px 0'}}/>
            <div className="flex flex-row items-center justify-end">
                <Button variant={"secondary"} disabled={settingsStore.settingsInflight} onClick={resetSettings} style={{ marginRight: '24px'}}>Reset</Button>
                <Button disabled={settingsStore.settingsInflight} onClick={onClickSaveSettings}>Save Settings</Button>
            </div>
        </>)}
        </div>
    </>
}


export default SettingsView