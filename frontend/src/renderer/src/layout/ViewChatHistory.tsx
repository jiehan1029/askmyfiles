import { Separator } from "@renderer/shared/components/ui/separator"


export function ChatHistoryView() {
    return <>
        <div className="p-2 pb-12 overflow-scroll">
            <p className="text-sm">View or continue on past conversations.</p>
            <Separator style={{ marginTop: '12px', marginBottom: '12px'}} />
            <div className="hover:bg-slate-200 border-solid border-2 rounded-lg p-2 my-4 w-[calc(100%-32px)]" style={{ marginTop: '12px'}}>
                <div className="text-sm italic">Apr 7, 2025</div>
                <div className="text-md h-[26px] overflow-y-hidden overflow-x-clip">Flight information</div>
            </div>
            <div className="hover:bg-slate-200 border-solid border-2 rounded-lg p-2 my-4 w-[calc(100%-32px)]" style={{ marginTop: '12px'}}>
                <div className="text-sm italic">Apr 7, 2025</div>
                <div className="text-md h-[26px] overflow-y-hidden overflow-x-clip">Flight information</div>
            </div>
        </div>
    </>
}


export default ChatHistoryView