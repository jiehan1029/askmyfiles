import GithubMark from '../assets/github-mark-white.svg'
import { Mail } from 'lucide-react'

export function AppFooter() {
    return <>
        <footer className="w-screen pl-4 pr-4 p-1 pb-1 flex flex-row items-center justify-center bg-primary text-primary-foreground" style={{ height: '30px'}}>
        <a href="https://github.com/jiehan1029/askmyfiles" target='_blank'><img alt="Github logo" className='w-[20px]' src={GithubMark} /></a>
        <a href="mailto:jiehan1029@gmail.com?subject=Feedback for AskMyFile" target='_blank'><Mail className="w-[20px]" style={{ marginRight: '20px', marginLeft: '20px'}} /></a>
        </footer>
    </>
}


export default AppFooter