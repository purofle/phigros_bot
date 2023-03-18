"""
Copyright 2022-2023 Purofle and contributors.

此源代码的使用受 GNU AFFERO GENERAL PUBLIC LICENSE version 3 许可证的约束, 可以在以下链接找到该许可证.
Use of this source code is governed by the GNU AGPLv3 license that can be found through the following link.

https://www.gnu.org/licenses/gpl-3.0.html
"""
import hashlib
import json
import logging
import random
import itertools
import sys
from typing import Any, Dict, List

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineQuery, InputTextMessageContent, InlineQueryResultArticle
from thefuzz import fuzz

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=sys.argv[1])
dp = Dispatcher(bot)

logging.info("读取 JSON 信息")
with open("phigros_bot/Phigros.json", "r") as f:
    raw_phigros_json = f.read()

phigros: Dict[str, Any] = json.loads(raw_phigros_json)
music_name = list(phigros.keys())
logging.info(f"谱面 JSON 信息加载完成，大小为{len(phigros)}")

with open("phigros_bot/tips.json", "r") as f:
    raw_tips_json = f.read()

raw_tips: Dict[str, List[str]] = json.loads(raw_tips_json)

# 将 raw_tips 展开为 List[str]
tips = list(itertools.chain.from_iterable(raw_tips.values()))

logging.info(f"Tips JSON 信息加载完成，大小为{len(tips)}")

info = {
        "歌名": "song",
        "曲绘": "illustration",
        "高清曲绘": "illustration_big",
        "BPM": "bpm",
        "曲师": "composer",
        "长度": "length",
        "画师": "illustrator",
    }

chart_info = {
        "等级": "level",
        "定数": "difficulty",
        "Max Combo": "combo",
        "谱师": "charter",
}


@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: types.Message):
    await message.reply("Hi!\n欢迎使用该 Bot! 请使用 inline 调用。\n")


@dp.message_handler(commands=["random"])
async def send_random(message: types.Message):
    random_song = random.sample(tuple(phigros.values()), 1)[0]

    basic_info = "\n".join([f"{i[0]}: {random_song.get(i[1])}" for i in info.items()])
    charts: Dict[str, Dict[str, str]] = random_song["chart"]
    chart_basic_info = ""
    for i in charts.keys():
        chart_basic_info += i + "\n"
        chart_basic_info += "\n".join(
            [f"{c[0]}: {charts[i].get(c[1])}" for c in chart_info.items()]
        )
        chart_basic_info += "\n\n"

    await message.reply(basic_info + "\n\n" + chart_basic_info.strip())


@dp.message_handler(commands=["tip"])
async def get_tip(message: types.Message):
    tip = random.sample(tips, 1)[0]
    await message.reply(tip)


@dp.inline_handler()
async def find_music(inline_query: InlineQuery):
    text = inline_query.query

    result_id: str = hashlib.md5(text.encode()).hexdigest()
    score = {}
    for i in music_name:
        score[i] = fuzz.token_sort_ratio(text, i.lower())
    # 给 dict 按照 value 排序
    sorted_score = sorted(score.items(), key=lambda x: x[1], reverse=True)
    name, score = sorted_score[0]
    music_info = phigros.get(name)

    if score == 0 or music_info is None:
        name = "未找到"
        item = InlineQueryResultArticle(
            id=result_id,
            title=name,
            input_message_content=InputTextMessageContent(
                f"输入的文本：{text}\n解析的歌曲：{name}\n匹配率：{score}"
            ),
        )
        await bot.answer_inline_query(inline_query.id, results=[item], cache_time=1)
        return

    basic_info = "\n".join([f"{i[0]}: {music_info.get(i[1])}" for i in info.items()])
    charts: Dict[str, Dict[str, str]] = music_info["chart"]

    items = []
    for i in charts.keys():
        chart_basic_info = "\n".join(
            [f"{c[0]}: {charts[i].get(c[1])}" for c in chart_info.items()]
        )
        result_id: str = hashlib.md5(i.encode()).hexdigest()
        items.append(
            InlineQueryResultArticle(
                id=result_id,
                title=f"{name} - {i}",
                input_message_content=InputTextMessageContent(
                    f"{basic_info}\n\n选择的难度：{i}\n{chart_basic_info}"
                ),
                thumb_url=music_info.get("illustration"),
            )
        )

    await bot.answer_inline_query(inline_query.id, results=items, cache_time=1)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
