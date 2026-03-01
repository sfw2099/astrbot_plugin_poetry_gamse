from astrbot.api.event import AstrMessageEvent

class BaseGame:
    def __init__(self, session_id, db, config, on_game_end_callback):
        self.session_id = session_id
        self.db = db
        self.config = config
        self.on_game_end_callback = on_game_end_callback
        self.timer_task = None
        
    def stop_game(self):
        """通用：终止游戏并销毁会话"""
        if self.timer_task:
            self.timer_task.cancel()
        self.on_game_end_callback(self.session_id)
        
    async def process_msg(self, event: AstrMessageEvent, msg_raw: str, user_id: str, user_name: str):
        """通用接口：处理玩家发送的普通消息。各游戏自行实现"""
        raise NotImplementedError
