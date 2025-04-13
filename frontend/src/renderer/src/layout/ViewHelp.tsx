import { Separator } from "@renderer/shared/components/ui/separator"
import GithubMark from '../assets/github-mark.svg'
import { Mail } from 'lucide-react'
import {
    Accordion,
    AccordionContent,
    AccordionItem,
    AccordionTrigger,
} from "@renderer/shared/components/ui/accordion"


export function HelpView() {
    return <>
        <div className="p-2 pb-12 overflow-scroll">
            <div className="flex flex-row justify-start items-center">
                <span className="text-sm">Contact Us:</span>
                <a href="https://github.com" target='_blank' style={{ marginRight: '20px', marginLeft: '20px'}}><img alt="Github logo" className='w-[20px]' src={GithubMark} /></a>
                <a href="mailto:jiehan1029@gmail.com?subject=Feedback for AskMyFile" target='_blank'><Mail className="w-[20px]" /></a>
            </div>
            <Separator style={{ marginTop: '12px', marginBottom: '12px'}} />
            <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="item-1">
                    <AccordionTrigger>Which LLM model does it support?</AccordionTrigger>
                    <AccordionContent>
                        You can run model in localhost or provide Google Analytc Studio's API token to use Gemini.
                    </AccordionContent>
                </AccordionItem>
            </Accordion>
        </div>
    </>
}


export default HelpView