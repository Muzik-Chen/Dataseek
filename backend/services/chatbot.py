"""
智能客服服务 — 管理对话状态、知识检索、回复生成。

当前为关键词匹配占位实现，后续通过 ai/ 模块接入：
- LangChain ChatModel（Qwen / DeepSeek）
- RAG 向量检索（FAISS / Chroma）
- 多轮对话记忆（ConversationBufferMemory）
"""
import secrets
from typing import AsyncGenerator


# === 潮汕文化知识库（后续迁移至向量数据库） ===
KNOWLEDGE = {
    # 美食类
    "牛肉火锅": {
        "answer": "潮汕牛肉火锅以新鲜为灵魂，牛肉从屠宰到上桌不超过4小时。必点部位：吊龙（嫩滑）、匙柄（弹牙）、胸口朥（爽脆）、五花趾（稀有）。蘸料：沙茶酱是灵魂。热门店铺：汕头八合里海记、福合埕、陈记顺和。",
        "tags": ["美食", "牛肉", "火锅"],
    },
    "肠粉": {
        "answer": "潮汕肠粉与广式肠粉不同，皮更薄更滑，馅料更丰富。常见馅料：牛肉、猪肉、虾仁、鸡蛋、生菜、豆芽。最后淋上秘制卤汁（非酱油），撒上菜脯粒。推荐：汕头小公园附近的老牌肠粉店。",
        "tags": ["美食", "小吃", "肠粉"],
    },
    "蚝烙": {
        "answer": "蚝烙是潮汕经典小吃，用新鲜生蚝+番薯粉浆+鸡蛋煎制而成，外酥内嫩。蘸鱼露+胡椒粉提鲜。汕头西堤路老牌蚝烙最为出名。",
        "tags": ["美食", "小吃", "海鲜"],
    },
    "粿条汤": {
        "answer": "粿条汤是潮汕人的日常主食，用米浆制成的粿条配以猪骨/鸡骨熬制的清汤，加猪肉片、猪肝、鱼丸、肉饼等配料，撒上葱花和炸蒜茸。一碗好的粿条汤，汤清味浓、粿条滑嫩。",
        "tags": ["美食", "主食", "粿"],
    },
    "卤鹅": {
        "answer": "潮汕卤鹅以澄海狮头鹅最为著名，用八角、桂皮、南姜等香料卤制，肉质紧实、卤香入骨。鹅肝、鹅翅、鹅掌是精华部位。推荐：汕头澄海区的老牌卤鹅店。",
        "tags": ["美食", "卤味", "鹅"],
    },
    "鸭母捻": {
        "answer": "鸭母捻是潮汕传统甜汤，类似汤圆但形状椭圆如鸭蛋。馅料有芝麻、花生、绿豆沙等，配以白果、莲子、薏米同煮，汤底清甜。潮州牌坊街的胡荣泉最为正宗。",
        "tags": ["美食", "甜品", "小吃"],
    },

    # 非遗类
    "英歌舞": {
        "answer": "英歌舞是国家级非物质文化遗产，融合武术、舞蹈、戏曲元素。表演者面绘梁山好汉脸谱，手持英歌槌，随锣鼓节奏变换阵型。最盛大的表演在春节至元宵期间，汕头潮阳区是主要传承地。",
        "tags": ["非遗", "舞蹈", "春节"],
    },
    "工夫茶": {
        "answer": "潮汕工夫茶是中国茶道'活化石'，讲究二十一式冲泡技法。核心要领：沸水淋罐（热罐）、高冲低斟（激出茶香）、关公巡城（均匀分茶）、韩信点兵（点滴不漏）。常用茶叶：凤凰单丛（乌龙茶）。体验地点：潮州古城的工夫茶体验馆。",
        "tags": ["非遗", "茶道", "体验"],
    },
    "潮剧": {
        "answer": "潮剧是用潮州方言演唱的古老戏曲剧种，属南戏分支，有500多年历史。唱腔优美、做工细腻，代表剧目有《荔镜记》《苏六娘》《张春郎削发》。汕头和潮州均有潮剧团定期演出。",
        "tags": ["非遗", "戏曲", "表演"],
    },
    "嵌瓷": {
        "answer": "嵌瓷（也称'贴饶'）是潮汕特有的建筑装饰工艺，用彩色碎瓷片在屋顶、墙壁镶嵌出人物花鸟、龙凤麒麟等图案，色彩鲜艳且数百年不褪色。汕头潮南区大寮村的嵌瓷工艺被列入国家级非遗。代表性传承人：许少雄。",
        "tags": ["非遗", "工艺", "建筑"],
    },
    "潮绣": {
        "answer": "潮绣是中国四大名绣之一粤绣的重要分支，以金线绣、绒线绣和线绣为主，作品富丽堂皇、立体感强。代表技法有垫高绣、双面绣等。潮州是主要传承地，可到潮绣博物馆参观体验。",
        "tags": ["非遗", "工艺", "刺绣"],
    },
    "木雕": {
        "answer": "潮汕木雕（金漆木雕）以多层镂空、金碧辉煌而闻名，是中国四大木雕之一。广泛用于建筑装饰、家具、神像雕刻。揭阳和潮州是主要产地。代表作可在潮州己略黄公祠欣赏。",
        "tags": ["非遗", "工艺", "雕刻"],
    },

    # 景点类
    "广济桥": {
        "answer": "广济桥（俗称湘子桥）位于潮州古城东门外，横跨韩江，是中国四大古桥之一。始建于南宋，集梁桥、浮桥、拱桥于一体，中间由18艘梭船连接，'十八梭船廿四洲'是其独特景观。门票：20元。开放时间：9:00-17:00。",
        "tags": ["景点", "潮州", "古桥"],
    },
    "南澳岛": {
        "answer": "南澳岛是广东省唯一的海岛县，拥有青澳湾（广东最美海湾）、总兵府（明清海防遗址）、宋井（南宋遗迹）等景点。推荐游玩1-3天，海鲜丰富新鲜。从汕头市区到南澳岛约1.5小时车程。",
        "tags": ["景点", "汕头", "海岛"],
    },
    "牌坊街": {
        "answer": "潮州牌坊街是中国牌坊最集中的历史文化街区，全长1948米，有22座明清风格石牌坊。沿街汇集了潮州老字号、非遗体验馆、工夫茶馆和传统小吃店，是感受潮州文化的必到之地。",
        "tags": ["景点", "潮州", "街区"],
    },
    "小公园": {
        "answer": "汕头小公园是汕头老城的核心地标，以中山纪念亭为中心呈放射状分布。骑楼建筑群融合中西风格，是'百年商埠'汕头的历史见证。周边汇集众多老字号美食，是美食探索的起点。",
        "tags": ["景点", "汕头", "骑楼"],
    },

    # 节日民俗类
    "营老爷": {
        "answer": "营老爷是潮汕地区最重要的传统民俗活动，在农历正月举行。各村各乡将庙中神像请出巡游，伴有英歌舞、锣鼓班、标旗队等表演。最热闹的是汕头澄海区和潮州潮安区的营老爷活动。",
        "tags": ["民俗", "春节", "巡游"],
    },
    "中秋": {
        "answer": "潮汕中秋有拜月娘的独特习俗，家家户户在庭院设案拜月，供品有月饼、芋头、水果等。孩子们提着灯笼走街串巷，热闹非凡。潮汕月饼（朥饼）以绿豆沙和猪肉为馅，酥皮层次分明。",
        "tags": ["民俗", "节日", "中秋"],
    },
    "元宵": {
        "answer": "潮汕元宵节有赏灯、猜灯谜、吃汤圆的习俗。各地会举办大型灯会，其中潮州古城灯会和汕头南澳渔灯节最为知名。'营灯'（游灯）是潮汕独特的元宵民俗。",
        "tags": ["民俗", "节日", "元宵"],
    },

    # 综合
    "潮汕": {
        "answer": "潮汕地区包括汕头、潮州、揭阳三市，位于广东省东部沿海，是著名的侨乡和文化之乡。潮汕文化体系完整、特色鲜明，涵盖工夫茶、潮剧、英歌舞、潮菜美食、嵌瓷、木雕、潮绣、抽纱等多个领域。潮汕话（潮州话）是闽南语系的重要分支。",
        "tags": ["综合", "地区"],
    },
    "旅游": {
        "answer": "潮汕旅游以'一城一岛一桥'为核心：潮州古城（广济桥+牌坊街+开元寺）、汕头南澳岛+小公园、揭阳学宫。建议游玩3-5天，最佳季节为10月-次年4月（秋冬季气候宜人）。美食是潮汕旅游的重头戏，建议每餐尝试不同品类。",
        "tags": ["综合", "旅游"],
    },
}

# 推荐问题列表
SUGGESTED_QUESTIONS = [
    "潮汕有什么必吃的美食？",
    "工夫茶有什么讲究？",
    "英歌舞什么时候有表演？",
    "潮汕3天怎么玩？",
    "潮汕有哪些非遗项目？",
    "牛肉火锅应该怎么点？",
]

WELCOME_MESSAGE = (
    "您好！我是潮汕文化小助手 🍵\n\n"
    "我可以帮您了解：\n"
    "• 🍲 潮汕美食（牛肉火锅、肠粉、蚝烙…）\n"
    "• 🎭 非遗文化（英歌舞、工夫茶、潮剧…）\n"
    "• 🏛️ 旅游景点（广济桥、南澳岛、牌坊街…）\n"
    "• 🎊 民俗节日（营老爷、中秋拜月娘…）\n\n"
    "随便问我什么吧～"
)


class ChatbotService:
    """智能客服对话服务。"""

    def __init__(self):
        self._sessions: dict[str, list[dict]] = {}  # session_id → messages

    def get_welcome(self) -> dict:
        """获取欢迎语和推荐问题。"""
        return {
            "welcome": WELCOME_MESSAGE,
            "suggestions": SUGGESTED_QUESTIONS,
        }

    async def chat(
        self,
        message: str,
        session_id: str = "",
    ) -> dict:
        """处理用户消息并返回回复。

        Args:
            message: 用户输入的消息
            session_id: 会话 ID（用于多轮对话上下文）

        Returns:
            {"reply": str, "sources": list[dict], "session_id": str}
        """
        if not session_id:
            session_id = secrets.token_hex(16)  # 加密安全的随机会话 ID

        # 检索知识库
        reply, sources = self._search_knowledge(message)

        # 保存会话历史
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        self._sessions[session_id].append({"role": "user", "content": message})
        self._sessions[session_id].append({"role": "assistant", "content": reply})

        # 限制历史长度
        if len(self._sessions[session_id]) > 50:
            self._sessions[session_id] = self._sessions[session_id][-50:]

        return {
            "reply": reply,
            "sources": sources,
            "session_id": session_id,
        }

    def _search_knowledge(self, query: str) -> tuple[str, list[dict]]:
        """关键词检索知识库（后续替换为向量检索）。

        Returns:
            (reply, sources)
        """
        # 按关键词长度降序匹配（优先匹配长关键词）
        matches = []
        for keyword, entry in sorted(KNOWLEDGE.items(), key=lambda x: -len(x[0])):
            if keyword in query:
                matches.append((keyword, entry))

        if matches:
            # 返回最佳匹配
            keyword, entry = matches[0]
            sources = [{"title": keyword, "type": "知识库", "tags": entry.get("tags", [])}]
            return entry["answer"], sources

        # 无匹配时的兜底回复
        return self._fallback_reply(query), []

    def _fallback_reply(self, query: str) -> str:
        """兜底回复 — 引导用户提问。"""
        return (
            f"关于「{query[:30]}」，我还在学习中 📚\n\n"
            f"您可以尝试问我：\n"
            f"• 潮汕有什么好吃的？\n"
            f"• 工夫茶怎么泡？\n"
            f"• 推荐旅游路线\n"
            f"• 英歌舞是什么？\n"
            f"• 最近有什么民俗活动？"
        )

    async def stream_chat(
        self,
        message: str,
        session_id: str = "",
    ) -> AsyncGenerator[str, None]:
        """流式生成回复（SSE，后续接入 LLM streaming）。"""
        result = await self.chat(message, session_id)
        # 模拟流式输出
        reply = result["reply"]
        chunk_size = 2
        for i in range(0, len(reply), chunk_size):
            yield reply[i:i + chunk_size]

    def get_history(self, session_id: str) -> list[dict]:
        """获取会话历史。"""
        return self._sessions.get(session_id, [])

    def clear_session(self, session_id: str) -> None:
        """清除会话历史。"""
        self._sessions.pop(session_id, None)
