import React, {useRef} from 'react'
import { Row, Col, Avatar, Button} from 'antd';
import {Message, Bot, theme_blue} from '../components/interface'
import MessageComponent from '../components/message_component';
import {defualt_user_avator, get_application_icon_src} from './api'
import ImageComponentPublic from './image_component_public'
import UIApplication from './ui_application';


interface Props {
    messages: Message[];
    tmp_message: Message | null;
    bot: Bot;
    chat_id: string;
  }


const MessageList: React.FC<Props> = (props) => {
    const messages = props.messages
    const tmp_message = props.tmp_message
    const bot = props.bot
    const applicatoin_icon_url = get_application_icon_src(bot)
    const [show_messages, setShowMessages] = React.useState<Message[]>([])
    const messagesDivRef = useRef<any>(null);
    // 当检测到页面没有在底部时，不进行自动滚动
    const [auto_scroll, setAutoScroll] = React.useState<boolean>(true)
    
    const add_count = 30

    React.useEffect(() => {
        if (messages) {
            setShowMessages(messages.slice(-add_count))
            // messagesDivRef.current.scrollIntoView({behavior: 'smooth', block: 'end', inline: 'nearest'});
            setTimeout(() => {
                // 滚动到底部
                if (messagesDivRef.current && auto_scroll) {
                    messagesDivRef.current.scrollTop = messagesDivRef.current.scrollHeight;
                }
            }, 10)
        }
    }, [messages])

    React.useEffect(() => {
        if (messagesDivRef.current && auto_scroll) {
            messagesDivRef.current.scrollTop = messagesDivRef.current.scrollHeight;
        }
    }, [tmp_message])

    const loadMore = () => {
        if (messages && messages.length > show_messages.length) {
            const show_count = Math.max(show_messages.length + add_count, 0)
            setShowMessages(messages.slice(-show_count))
        }
    }

    const onScroll = (e: React.UIEvent<HTMLElement, UIEvent>) => {
        // 如果滚动到顶部，加载更多
        const scrollTop = e.currentTarget.scrollTop
        const currentHeight = e.currentTarget.scrollHeight
        // const clientHeight = e.currentTarget.clientHeight
        // console.log(scrollTop);
        if (scrollTop === 0) {
            loadMore()
            setTimeout(()=>{
                // 新高度
                const toTop = messagesDivRef.current.scrollHeight - currentHeight;
                messagesDivRef.current.scrollTop = toTop;
            }, 100)
        }
        // 如果滚动到底部，自动滚动
        if (scrollTop + 1 >= currentHeight - e.currentTarget.clientHeight) {
            setAutoScroll(true)
        } else {
            setAutoScroll(false)
        }
      };

    const avator_style = {
        marginRight: 0, 
        borderRadius: '20%',
        width: 30
    }

    // <div style={{height: 20}}><Button type='link' onClick={loadMore}>加载更多</Button></div> 
    const showMore = (<div style={{height: 20, margin: 10}}>下滑显示更多</div>)
    const noMore = (<div style={{height: 20, margin: 10}}>没有更多消息了</div>)

    const is_application = props?.bot?.type == 'application';

    return (
    <div style={{height: is_application ? 'calc(100vh - 80px)' : 'calc(100vh - 130px)', overflow: 'scroll', paddingBottom: 20}} ref={messagesDivRef} onScroll={onScroll} >
        {/* {show_messages && messages && show_messages.length < messages.length ? showMore : null} */}
        {show_messages && show_messages.map((message: Message, index: number) => {
            return (
                <Row
                    style={{ padding: 8, borderBottom: (((index === show_messages.length - 1) && (!tmp_message)) && !is_application)? "none" : "1px solid #F0F0FF" }}
                    key={message.id}
                >
                    <Col span={1}>
                        <div style={{height: 30}}>
                            <ImageComponentPublic style={avator_style}  src={(message.role === 'bot') ? applicatoin_icon_url : defualt_user_avator} />
                        </div>
                    </Col>
                    <Col span={23} style={{wordWrap: 'break-word', marginTop:-2, paddingLeft: 5, textAlign: 'left', lineHeight: '1.5'}}>
                        <div style={{fontSize: 14, paddingBottom: 8, color: theme_blue}}>{message.create_at?.slice(0, 19)}</div>
                        <MessageComponent message={message} />
                    </Col>
                </Row>
            )
        })}
        {/* 显示tmp_message */}
        {tmp_message && (
            <Row style={{ padding: 8, backgroundColor: '#FFFFEF'}} >
                <Col span={1}>
                    <div style={{height: 30}}>
                        <ImageComponentPublic style={avator_style}  src={(tmp_message.role === 'bot') ? applicatoin_icon_url : defualt_user_avator} />
                    </div>
                </Col>
                <Col span={23} style={{wordWrap: 'break-word', marginTop: 5, paddingLeft: 5, textAlign: 'left', lineHeight: '1.5'}}>
                    <div style={{fontSize: 14, paddingBottom: 8, color: theme_blue}}>{tmp_message.create_at?.slice(0, 19)}</div>
                    <MessageComponent message={tmp_message} />
                </Col>
            </Row>
        )}
        {is_application && (
            <Row style={{ padding: 8}} >
                <Col span={1}>
                    <div style={{height: 30}}>
                        <ImageComponentPublic style={avator_style}  src={defualt_user_avator} />
                    </div>
                </Col>
                <Col span={23} style={{wordWrap: 'break-word', marginTop: 5, paddingLeft: 5, textAlign: 'left', lineHeight: '1.5'}}>
                    <UIApplication bot={props.bot} chat_id={props.chat_id}/>
                </Col>
            </Row>
        )}
    </div>)
}

export default MessageList