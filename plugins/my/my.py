# encoding:gbk
import threading
import requests
import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from plugins import *
from reloading import reloading

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
                config_path = os.path.join(curdir, "config.json")
                if not os.path.exists(config_path):
                    conf = {"src_url": "www.baidu.com"}
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
        # 获取消息
        content_search = context["context"].content.strip()
        logger.info(f"[my]当前监听信息： {content_search}")

        if any(content_search.startswith(prefix) for prefix in ["搜剧", "搜", "全网搜"]) and not content_search.startswith("搜索"):

            def process_string2(s):
                # 判断是否包含@
                if '@' in s:
                    # 找到@字符的位置
                    index = s.index('@')
                    # 删除包含@在内后面的所有字符
                    return s[:index]
                else:
                    return s

            def search_question(question):
                url = 'https://www.xinyueso.com/api/search'
                params = {
                    'is_time': '1',
                    'page_no': '1',
                    'page_size': '5',
                    'title': question
                }
                try:
                    response = requests.get(url, params=params)
                    response.raise_for_status()  # 检查请求是否成功
                    responseData = response.json().get('data', {}).get('items', [])
                    return responseData
                except requests.exceptions.RequestException as e:
                    print(f"Error fetching data: {e}")
                    return []

            def search_alone(question):
                url = 'https://www.xinyueso.com/api/other/all_search'
                payload = {
                    'title': question
                }
                try:
                    response = requests.post(url, json=payload)
                    response.raise_for_status()
                    responseData = response.json().get('data', [])
                    return responseData
                except requests.exceptions.RequestException as e:
                    print(f"Error fetching data: {e}")
                    return []

            def remove_prefix(content, prefixes):
                for prefix in prefixes:
                    if content.startswith(prefix):
                        return content[len(prefix):].strip()
                return content.strip()

            def perform_search():
                # 初次搜索
                response_data = search_question(contentSearch) if not content_search.startswith("全网搜") else []
                if not response_data:
                    # 通知用户深入搜索
                    reply_text2 = f"@{user_nickname}\n正在深入搜索，请稍等..."
                    self._send_reply(context, Reply(ReplyType.TEXT, reply_text2))

                    # 启动线程进行第二次搜索
                    def perform_second_search():
                        response_data = search_alone(contentSearch)
                        send_final_reply(response_data, reply_text, context)

                    second_search_thread = threading.Thread(target=perform_second_search)
                    second_search_thread.start()
                else:
                    # 如果第一次搜索找到结果，发送最终回复
                    send_final_reply(response_data, reply_text, context)

            def send_final_reply(response_data, reply_text, context):
                is_times = 0
                if not response_data:
                    reply_text_final = f"{reply_text}\n未找到，可换个关键词尝试哦~"
                    reply_text_final += "\n??宁少写，不多写、错写~"
                    reply_text_final += "\n--------------------"
                    reply_text_final += "\n可访问以下链接提交资源需求"
                    reply_text_final += "\nhttps://www.xinyueso.com"
                else:
                    reply_text_final = f"{reply_text}\n--------------------"
                    for item in response_data:
                        if item.get('is_time') == 1:
                            reply_text_final += f"\n ?? {item.get('title', '未知标题')}"
                            is_times += 1
                        else:
                            reply_text_final += f"\n{item.get('title', '未知标题')}"
                        reply_text_final += f"\n{item.get('url', '未知URL')}"
                        reply_text_final += "\n--------------------"

                    if is_times > 0:
                        reply_text_final += "\n ??资源来源网络，30分钟后删除"
                        reply_text_final += "\n--------------------"
                    else:
                        reply_text_final += "\n 不是短剧？请尝试：全网搜XX"
                        reply_text_final += "\n--------------------"

                    reply_text_final += "\n欢迎观看！如果喜欢可以喊你的朋友一起来哦"

                reply = Reply(ReplyType.TEXT, reply_text_final)
                self._send_reply(context, reply)

            content_search = process_string2(content_search)
            user_nickname = context['msg'].actual_user_nickname
            reply_text = f"@{user_nickname}"
            contentSearch = remove_prefix(content_search, ["搜剧", "搜", "全网搜"]).strip()


            # 启动线程执行第一次搜索
            first_search_thread = threading.Thread(target=perform_search)
            first_search_thread.start()
            return None




        # if "搜" in content:
        #     reply = Reply(ReplyType.TEXT, f"url: {self.src_url}")
        #     e_context["reply"] = reply
        #     e_context.action = EventAction.BREAK_PASS
        # elif "全网搜" in content:
        #     logger.info("不处理")
        #     e_context["reply"] = None
        #     e_context.action = EventAction.BREAK_PASS
        # elif "问" in content:
        #     e_context["reply"] = None
        #     e_context.action = EventAction.CONTINUE
        # return




    def get_help_text(self, **kwargs):
        return "自定义功能"
