import json
from pathlib import Path
from nonebot.adapters.onebot.v11 import Message
from nonebot.log import logger

init_data = {
    "data": []
}


class followerData(object):
    def __init__(self):
        self.data_dir = Path("data/bilibili_follower").absolute()
        self.data_path = self.data_dir / "data.json"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.data = {}
        self.load()

    def load(self):
        if self.data_path.exists() and self.data_path.is_file():
            with self.data_path.open("r", encoding="utf-8") as f:
                self.data = json.load(f)
            logger.success("读取数据位于 " + str(self.data_path))
        else:
            self.data = init_data
            self.save()
            logger.success("创建数据位于 " + str(self.data_path))

    def save(self):
        with self.data_path.open("w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)
