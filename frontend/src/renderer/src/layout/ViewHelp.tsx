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
                <span className="text-sm">Contact Me:</span>
                <a href="https://github.com" target='_blank' style={{ marginRight: '20px', marginLeft: '20px'}}><img alt="Github logo" className='w-[20px]' src={GithubMark} /></a>
                <a href="mailto:jiehan1029@gmail.com?subject=Feedback for AskMyFile" target='_blank'><Mail className="w-[20px]" /></a>
            </div>
            <Separator style={{ marginTop: '12px', marginBottom: '12px'}} />
            <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="item-1">
                    <AccordionTrigger>Why use AskMyFiles?</AccordionTrigger>
                    <AccordionContent>
                        Chat with your files and get instant answers. Sync folders, search with AI, and choose between cloud or fully local models. It's fast, flexible, and keeps your data private.
                        <li>Get insights directly from your own documents</li>
                        <li>Connect to powerful cloud models using your API key (Gemini, Hugging Face, etc.)</li>
                        <li>Or run everything locally with your own LLM — nothing ever leaves your machine</li>
                    </AccordionContent>
                </AccordionItem>
                <AccordionItem value="item-2">
                    <AccordionTrigger>Which LLM providers does it support?</AccordionTrigger>
                    <AccordionContent>
                        At this moment, AskMyFiles supports Gemini, HuggingFace, and any self-hosted models that you spin up in the associated Ollama container.
                        Open the settings tab from sidebar to configure.
                    </AccordionContent>
                </AccordionItem>
                <AccordionItem value="item-3">
                    <AccordionTrigger>What file types does it support?</AccordionTrigger>
                    <AccordionContent>
                        The files of the following types could be parsed and used in generating answers: text/plain", text/html, application/pdf, text/markdown.
                    </AccordionContent>
                </AccordionItem>
                <AccordionItem value="item-4">
                    <AccordionTrigger>How can I give feedback?</AccordionTrigger>
                    <AccordionContent>
                        You can open a GitHub issue or shoot me an email!
                        This is just a side project I tinker with after work, so I might be a little slow to reply — but I really appreciate the feedback!
                    </AccordionContent>
                </AccordionItem>
            </Accordion>
        </div>
    </>
}


export default HelpView