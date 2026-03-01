import os
import asyncio
import aiohttp
import json

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register, StarTools
from astrbot.api import logger, AstrBotConfig

from .database import PoetryDB
from .game.flowing_petals import FlowingPetalsEngine
from .game.crossword_poetry import PoetryCrosswordEngine

@register("astrbot_plugin_poetry_games", "ALin", "诗词游戏引擎", "3.5.0")
class PoetryPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        
        # 获取标准数据目录
        self.plugin_data_dir = StarTools.get_data_dir("astrbot_plugin_poetry_games")
        self.plugin_data_dir.mkdir(parents=True, exist_ok=True)
        self.db_file = self.plugin_data_dir / 'poetry_data.db'
        
        # 存档目录配置
        self.saves_dir = self.plugin_data_dir / 'saves'
        self.saves_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据库下载链接
        self.download_url = "https://mirror.ghproxy.com/https://github.com/sfw2099/astrbot_plugin_poetry_games/releases/download/%E8%AF%97%E8%AF%8D%E6%95%B0%E6%8D%AE/poetry_data.db"
        
        self.db = None
        self.active_games = {} # 统一存放两类游戏引擎
        
        # 异步启动准备任务
        asyncio.create_task(self.prepare_database())

    async def prepare_database(self):
        """检查并准备数据库：直接下载 .db 文件并显示进度"""
        if self.db_file.exists() and self.db_file.stat().st_size > 0:
            try:
                self.db = PoetryDB(str(self.db_file))
                logger.info("✅ 数据库已就绪。")
                return
            except Exception:
                logger.warning("⚠️ 检测到损坏的数据库文件，准备重新下载...")
                os.remove(self.db_file)

        logger.info(f"📡 正在从 Release 下载数据库，请稍候 (文件较大，可能需要几分钟)...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.download_url) as resp:
                    if resp.status != 200:
                        logger.error(f"❌ 下载失败，状态码: {resp.status}。请检查链接是否有效。")
                        return
                    
                    total_size = int(resp.headers.get('Content-Length', 0))
                    downloaded_size = 0
                    last_log_percent = 0
                    
                    with open(self.db_file, "wb") as f:
                        while True:
                            chunk = await resp.content.read(8192)
                            if not chunk: 
                                break
                            
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            
                            if total_size > 0:
                                percent = int((downloaded_size / total_size) * 100)
                                if percent >= last_log_percent + 10:
                                    mb_downloaded = downloaded_size / (1024 * 1024)
                                    mb_total = total_size / (1024 * 1024)
                                    logger.info(f"⏳ 数据库下载进度: {percent}% ({mb_downloaded:.1f}MB / {mb_total:.1f}MB)")
                                    last_log_percent = percent
                            else:
                                mb_downloaded = downloaded_size / (1024 * 1024)
                                if mb_downloaded >= last_log_percent + 50:
                                    logger.info(f"⏳ 已下载: {mb_downloaded:.1f}MB...")
                                    last_log_percent = int(mb_downloaded)
            
            self.db = PoetryDB(str(self.db_file))
            logger.info("✅ 数据库下载并加载成功！")
            
        except Exception as e:
            logger.error(f"❌ 自动下载数据库失败: {e}")

    # ==========================================
    # 基础信息检索 (通用指令)
    # ==========================================
    @filter.command("查询诗句")
    async def find_sentence(self, event: AstrMessageEvent, sentence: str):
        if not self.db: 
            yield event.plain_result("数据库正在从 GitHub 赶来（首次运行下载中），请稍后再试...")
            return
        results = self.db.search_by_sentence(sentence)
        if not results:
            yield event.plain_result(f"未找到包含“{sentence}”的内容。")
            return
        resp = ["查询结果："]
        for title, author, dynasty in results:
            resp.append(f"• [{dynasty}] {author} —— 《{title}》")
        yield event.plain_result("\n".join(resp))

    @filter.command("查询诗词")
    async def find_full_poem(self, event: AstrMessageEvent, title_kw: str):
        if not self.db: 
            yield event.plain_result("数据库正在从 GitHub 赶来（首次运行下载中），请稍后再试...")
            return
        results = self.db.get_poem_by_title(title_kw)
        if not results:
            yield event.plain_result(f"未找到标题包含“{title_kw}”的诗词。")
            return
        resp = ["检索结果：\n" + "="*20]
        for i, (title, author, dynasty, content) in enumerate(results):
            clean_content = content.replace('\r\n', '\n').strip()
            resp.append(f"《{title}》\n作者：[{dynasty}] {author}\n\n{clean_content}")
            if i < len(results) - 1: resp.append("-" * 15)
        yield event.plain_result("\n".join(resp))

    # ==========================================
    # 游戏建局指令
    # ==========================================
    @filter.command("衔字飞花令")
    async def start_flowing(self, event: AstrMessageEvent):
        if not self.db:
            yield event.plain_result("⏳ 数据库加载中，请稍后再试...")
            return
            
        session_id = str(event.get_group_id() or event.get_session_id())
        if session_id in self.active_games:
            yield event.plain_result("当前群聊已有游戏正在进行！")
            return
            
        engine = FlowingPetalsEngine(session_id, self.db, str(self.saves_dir))
        self.active_games[session_id] = engine
        yield event.plain_result("🌸 【衔字飞花令】已建立！\n请群友发送【加入】参与排队，随时可加！第一位加入的玩家即可开始。")

    @filter.command("纵横飞花令")
    async def start_crossword(self, event: AstrMessageEvent):
        if not self.db:
            yield event.plain_result("⏳ 数据库加载中，请稍后再试...")
            return
            
        session_id = str(event.get_group_id() or event.get_session_id())
        if session_id in self.active_games:
            yield event.plain_result("当前群聊已有游戏正在进行！")
            return
            
        engine = PoetryCrosswordEngine(session_id, self.db, str(self.saves_dir))
        self.active_games[session_id] = engine
        yield event.plain_result("🌟 【纵横飞花令】已建立！\n请群友发送【加入】参与排队。第一名加入的玩家即可开始接龙！")
        
        # 触发渲染首张带有系统开局字样的图片并发送
        res = engine.step("ignore", "", "") 
        if res and "image" in res:
            yield event.image_result(res["image"])

    # ==========================================
    # 游戏管理指令
    # ==========================================
    @filter.command("恢复游戏")
    async def load_game(self, event: AstrMessageEvent):
        session_id = str(event.get_group_id() or event.get_session_id())
        if session_id in self.active_games:
            yield event.plain_result("当前已有进行中的游戏，请先【结束游戏】。")
            return
            
        save_file = os.path.join(str(self.saves_dir), f"game_{session_id}.json")
        if not os.path.exists(save_file):
            yield event.plain_result("未找到该群的存档文件。")
            return
            
        try:
            with open(save_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if "Crossword" in data.get("game_type", ""):
                engine = PoetryCrosswordEngine(session_id, self.db, str(self.saves_dir))
            else:
                engine = FlowingPetalsEngine(session_id, self.db, str(self.saves_dir))
                
            if engine.load_state():
                self.active_games[session_id] = engine
                yield event.plain_result("💾 进度恢复成功！游戏继续。")
            else:
                yield event.plain_result("❌ 存档文件读取失败。")
        except Exception as e:
            yield event.plain_result(f"❌ 恢复失败: {e}")

    @filter.command("生成战报")
    async def generate_report(self, event: AstrMessageEvent):
        session_id = str(event.get_group_id() or event.get_session_id())
        engine = self.active_games.get(session_id)
        if not engine:
            yield event.plain_result("当前没有进行中的游戏。如果要生成旧战报，请先【恢复游戏】。")
            return
        yield event.plain_result(engine.generate_text_report())

    @filter.command("结束游戏")
    async def stop_game(self, event: AstrMessageEvent):
        session_id = str(event.get_group_id() or event.get_session_id())
        if session_id in self.active_games:
            engine = self.active_games.pop(session_id)
            yield event.plain_result("⏹️ 游戏已结束。最后战果：\n" + engine.generate_text_report())
        else:
            yield event.plain_result("当前没有正在进行的游戏。")

    # ==========================================
    # 全局监听分发中枢
    # ==========================================
    @filter.event_message_type(filter.EventMessageType.ALL)
    async def handle_recv_msg(self, event: AstrMessageEvent):
        msg_raw = event.message_str.strip()
        # 忽略聊天括号和斜杠指令
        if msg_raw.startswith(("(", "（")) and msg_raw.endswith((")", "）")): return
        if not msg_raw or msg_raw.startswith(("/", "查询", "生成战报", "恢复", "结束", "纵横", "衔字")): return

        session_id = str(event.get_group_id() or event.get_session_id())
        if session_id not in self.active_games: return

        engine = self.active_games[session_id]
        user_id = str(event.get_sender_id())
        user_name = event.get_sender_name()

        # 拦截通用的【加入】口令
        if msg_raw in ["加入", "+加入", "1+加入", "1 + 加入"]:
            response = engine.step("join", user_id, user_name)
        else:
            response = engine.step("play", user_id, user_name, msg_raw)
            
        if not response: return
        
        if response.get("status") == "ignore": return
        if response.get("msg"): yield event.plain_result(response["msg"])
        if "image" in response: yield event.image_result(response["image"])