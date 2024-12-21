# encoding:utf-8
import threading
import requests
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from channel.wechat.wechat_channel import WechatChannel
import plugins
from plugins import *
from common.log import logger


@plugins.register(
    name="My",
    desire_priority=100,
    hidden=True,
    desc="自定义插件功能",
    version="1.0",
    author="lei",
)
class My(Plugin):
    def __init__(self):
        super().__init__()
        try:
            # load config
            conf = super().load_config()
            curdir = os.path.dirname(__file__)
            if not conf:
                # 配置不存在则写入默认配置
                logger.info("配置不存在则写入默认配置")
                config_path = os.path.join(curdir, "config.json")
                if not os.path.exists(config_path):
                    conf = {"src_url": "ks.jizhi.me1"}
                    with open(config_path, "w") as f:
                        json.dump(conf, f, indent=4)

            self.src_url = conf["src_url"]
            logger.info(f"src_url:   {self.src_url}")
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
            logger.info("[My] inited")
        except Exception as e:
            logger.warn("[My] init failed")
            raise e

    # 这个事件主要用于处理上下文信息。当用户发送消息时，系统会触发这个事件，以便根据上下文来决定如何响应用户的请求。它通常用于获取和管理对话的上下文状态。
    def on_handle_context(self, context: EventContext):
        if context["context"].type not in [
            ContextType.TEXT,
        ]:
            return

        # 发送文本
        def wx_send(reply_content):
            WechatChannel().send(Reply(ReplyType.TEXT, reply_content), context["context"])

        # 获取消息
        msg_content = context["context"].content.strip()
        logger.info(f"[my]当前监听信息： {msg_content}")
        logger.info(f'[my]当前配置conf： {conf()}')
        logger.info(f'[my]当前配置src_url： {conf().get("src_url")}')

        # "搜剧", "搜", "全网搜"
        if any(msg_content.startswith(prefix) for prefix in ["搜剧", "搜", "全网搜"]) and not msg_content.startswith("搜索"):
            # 获取用户名
            user_nickname = str(context["context"]["msg"].actual_user_nickname)
            at_name = ('@' + user_nickname) if not user_nickname else ''

            # 移除前缀
            def remove_prefix(content, prefixes):
                for prefix in prefixes:
                    if content.startswith(prefix):
                        return content[len(prefix):].strip()
                return content.strip()

            # 搜索内容
            search_content = remove_prefix(msg_content, ["搜剧", "搜", "全网搜"]).strip()

            # http 搜索资源
            def to_search(title):
                url = f'https://{conf().get("src_url")}/api/search'
                params = {
                    'is_time': '1',
                    'page_no': '1',
                    'page_size': '5',
                    'title': title
                }
                try:
                    response = requests.get(url, params=params)
                    response.raise_for_status()  # 检查请求是否成功
                    response_data = response.json().get('data', {}).get('items', [])
                    return response_data
                except requests.exceptions.RequestException as e:
                    print(f"Error fetching data: {e}")
                    return []

            # http 全网搜
            def to_search_all(title):
                url = f'https://{conf().get("src_url")}/api/other/all_search'
                payload = {
                    'title': title
                }
                try:
                    response = requests.post(url, json=payload)
                    response.raise_for_status()
                    response_data = response.json().get('data', [])
                    return response_data
                except requests.exceptions.RequestException as e:
                    print(f"Error fetching data: {e}")
                    return []

            # 回复内容
            def send_build(response_data):
                if not response_data:
                    reply_text_final = f"{at_name}搜索内容：{search_content}"
                    reply_text_final += "\n呜呜，还没找到呢~😔"
                    reply_text_final += "\n⚠关键词错误或存在错别字"
                    reply_text_final += "\n--------------------"
                    reply_text_final += "\n⚠搜短剧指令：搜:XXX"
                    reply_text_final += f"\n其他资源指令：全网搜:XX"
                else:
                    reply_text_final = f"{at_name} 搜索内容：{search_content}\n--------------------"
                    for item in response_data:
                        reply_text_final += f"\n 🌐️{item.get('title', '未知标题')}"
                        reply_text_final += f"\n{item.get('url', '未知URL')}"
                        reply_text_final += "\n--------------------"
                    if 'is_time=0' in str(response_data):
                        reply_text_final += "\n 🌐️资源来源网络，30分钟后删除请及时保存~"
                        reply_text_final += "\n--------------------"
                    else:
                        reply_text_final += "\n 不是短剧？请尝试：全网搜XX"
                        reply_text_final += "\n--------------------"

                    reply_text_final += "\n欢迎观看！如果喜欢可以喊你的朋友一起来哦"
                wx_send(reply_text_final)

            # 执行搜索
            def perform_search():
                response_data = to_search(search_content) if not msg_content.startswith("全网搜") else []
                if not response_data:
                    # 通知用户深入搜索
                    wx_send(f"{at_name} 🔍正在努力翻找中，请稍等一下下哦~🐾✨")

                    # 启动线程进行第二次搜索
                    threading.Thread(target=send_build(to_search_all(search_content))).start()
                else:
                    # 如果第一次搜索找到结果，发送最终回复
                    send_build(response_data)

            # 启动线程执行第一次搜索
            threading.Thread(target=perform_search()).start()

            context["reply"] = None
            context.action = EventAction.BREAK_PASS
            return

    def get_help_text(self, **kwargs):
        return "自定义功能"
