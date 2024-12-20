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
    desc="�Զ���������",
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
                # ���ò�������д��Ĭ������
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

    # ����¼���Ҫ���ڴ�����������Ϣ�����û�������Ϣʱ��ϵͳ�ᴥ������¼����Ա���������������������Ӧ�û���������ͨ�����ڻ�ȡ�͹���Ի���������״̬��
    def on_handle_context(self, context: EventContext):
        if context["context"].type not in [
            ContextType.TEXT,
        ]:
            return
        # ��ȡ��Ϣ
        content_search = context["context"].content.strip()
        logger.info(f"[my]��ǰ������Ϣ�� {content_search}")

        if any(content_search.startswith(prefix) for prefix in ["�Ѿ�", "��", "ȫ����"]) and not content_search.startswith("����"):

            def process_string2(s):
                # �ж��Ƿ����@
                if '@' in s:
                    # �ҵ�@�ַ���λ��
                    index = s.index('@')
                    # ɾ������@���ں���������ַ�
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
                    response.raise_for_status()  # ��������Ƿ�ɹ�
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
                # ��������
                response_data = search_question(contentSearch) if not content_search.startswith("ȫ����") else []
                if not response_data:
                    # ֪ͨ�û���������
                    reply_text2 = f"@{user_nickname}\n�����������������Ե�..."
                    self._send_reply(context, Reply(ReplyType.TEXT, reply_text2))

                    # �����߳̽��еڶ�������
                    def perform_second_search():
                        response_data = search_alone(contentSearch)
                        send_final_reply(response_data, reply_text, context)

                    second_search_thread = threading.Thread(target=perform_second_search)
                    second_search_thread.start()
                else:
                    # �����һ�������ҵ�������������ջظ�
                    send_final_reply(response_data, reply_text, context)

            def send_final_reply(response_data, reply_text, context):
                is_times = 0
                if not response_data:
                    reply_text_final = f"{reply_text}\nδ�ҵ����ɻ����ؼ��ʳ���Ŷ~"
                    reply_text_final += "\n??����д������д����д~"
                    reply_text_final += "\n--------------------"
                    reply_text_final += "\n�ɷ������������ύ��Դ����"
                    reply_text_final += "\nhttps://www.xinyueso.com"
                else:
                    reply_text_final = f"{reply_text}\n--------------------"
                    for item in response_data:
                        if item.get('is_time') == 1:
                            reply_text_final += f"\n ?? {item.get('title', 'δ֪����')}"
                            is_times += 1
                        else:
                            reply_text_final += f"\n{item.get('title', 'δ֪����')}"
                        reply_text_final += f"\n{item.get('url', 'δ֪URL')}"
                        reply_text_final += "\n--------------------"

                    if is_times > 0:
                        reply_text_final += "\n ??��Դ��Դ���磬30���Ӻ�ɾ��"
                        reply_text_final += "\n--------------------"
                    else:
                        reply_text_final += "\n ���Ƕ̾磿�볢�ԣ�ȫ����XX"
                        reply_text_final += "\n--------------------"

                    reply_text_final += "\n��ӭ�ۿ������ϲ�����Ժ��������һ����Ŷ"

                reply = Reply(ReplyType.TEXT, reply_text_final)
                self._send_reply(context, reply)

            content_search = process_string2(content_search)
            user_nickname = context['msg'].actual_user_nickname
            reply_text = f"@{user_nickname}"
            contentSearch = remove_prefix(content_search, ["�Ѿ�", "��", "ȫ����"]).strip()


            # �����߳�ִ�е�һ������
            first_search_thread = threading.Thread(target=perform_search)
            first_search_thread.start()
            return None




        # if "��" in content:
        #     reply = Reply(ReplyType.TEXT, f"url: {self.src_url}")
        #     e_context["reply"] = reply
        #     e_context.action = EventAction.BREAK_PASS
        # elif "ȫ����" in content:
        #     logger.info("������")
        #     e_context["reply"] = None
        #     e_context.action = EventAction.BREAK_PASS
        # elif "��" in content:
        #     e_context["reply"] = None
        #     e_context.action = EventAction.CONTINUE
        # return




    def get_help_text(self, **kwargs):
        return "�Զ��幦��"
