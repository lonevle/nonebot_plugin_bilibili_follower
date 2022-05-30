from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, MessageEvent
from nonebot.adapters.onebot.v11.permission import (
    GROUP_ADMIN,
    GROUP_OWNER,
    PRIVATE_FRIEND,
    GROUP,
)
from nonebot.rule import to_me
from nonebot.log import logger
from nonebot import require
from .data_source import followerData
from nonebot import on_command
import httpx
import random
import nonebot
from nonebot.permission import SUPERUSER
follower_data = followerData()

scheduler = require("nonebot_plugin_apscheduler").scheduler

new_follower = [
    "恭喜主人新增加%s个粉丝, 现在有%s个粉丝了",
    "主人粉丝数增加了%s位，现在是%s粉丝了，真是太厉害了",
    "耶，主人新增%s粉丝, 已经是%s粉的大up了",
    "欧尼酱，粉丝又涨了%s，有%s的粉丝了呢",
    "主人粉丝又涨了%s，有%s的粉丝喜欢主人了呢"
]
reduce_follower = [
    "呜呜，主人的有%s个粉丝取关了",
    "主人，有%s个粉丝离开了您，别伤心，我会一直在的呢",
    "主人，有%s个粉丝不喜欢您了，不过我一直喜欢主人的~",
    "刚刚有%s个粉丝离开了您，不过我一直陪着主人的~"
]


async def get_follower(uid):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36 Edg/95.0.1020.53"
    }
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url="https://api.bilibili.com/x/relation/stat?vmid=%s" % uid, headers=headers)
            r_json = r.json()
            if r_json["code"] == 0:
                # print(r_json["data"]["follower"])
                return r_json["data"]["follower"]
            else:
                logger.warning(f"获取粉丝数失败：{r_json}")
    except Exception as e:
        logger.warning(f"获取粉丝数失败,{e}")
        return False

async def main():
    for m in follower_data.data["data"]:
        follower = await get_follower(m["uid"])
        if follower is False:
            return False
        else:
            if m["follower"] != follower: #粉丝数有变化
                if m["follower"] != 0: # 已经记录过粉丝数
                    if follower > m["follower"]: # add
                        msg = random.choice(new_follower) % (follower-m["follower"], follower)
                    else:
                        msg = random.choice(reduce_follower) % (follower-m["follower"])
                else:
                    # print("初始化")
                    msg = "主人当前有%s个粉丝了呢，距离百万粉丝只差一步，加油啊！" % follower
                for qq in m["qq_list"]:
                    await nonebot.get_bot().send_private_msg(user_id=qq, message=Message(msg))
                for qq_group in m["group_list"]:
                    await nonebot.get_bot().send_group_msg(group_id=qq_group, message=Message("[CQ:at,qq=%s]" % m["qq"] + msg))
                        
                m["follower"] = follower
                follower_data.save()
            
def add_uid(uid, qq, group_list="", qq_list=""):
    if not (uid and qq and (group_list or qq_list)):
        print("数据不全")
        return False
    for e in follower_data.data["data"]:
        if e["uid"] == uid:
            if group_list and group_list not in e["group_list"]:
                e["group_list"].append(group_list)
                follower_data.save()
                return True
            elif qq_list and qq_list not in e["qq_list"]:
                e["qq_list"].append(qq_list)
                follower_data.save()
                return True
            else:
                return False
    if group_list:
        follower_data.data["data"].append({
            "uid": uid,
            "qq": qq,
            "follower": 0,
            "group_list": [group_list],
            "qq_list": []
        })
        
    else:
        follower_data.data["data"].append({
            "uid": uid,
            "qq": qq,
            "follower": 0,
            "group_list": [],
            "qq_list": [qq_list]
        })
    follower_data.save()
    return True

def del_uid(uid, qq):
    for e in follower_data.data["data"]:
        if e["uid"] == uid and e["qq"] == qq:
            follower_data.data["data"].remove(e)
            follower_data.save()
            return True
    return False
            

# 新增: bili add uid数字
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent, PrivateMessageEvent
bili = on_command("bili", permission=SUPERUSER|GROUP_ADMIN|GROUP_OWNER|PRIVATE_FRIEND|GROUP, block=False, priority=10)
@bili.handle()
async def _(bot: Bot, event: Event):
    get_qq = event.get_user_id()
    get_group = event.get_session_id()
    if get_qq == get_group: # 私聊
        is_group = False
    else:
        is_group = True
        try:
            group_id = get_group.split("_")[1]
            if not group_id or group_id == get_qq:
                return False
        except Exception as e:
            logger.warning(f"获取群号失败,{e}")
    
    args_list = event.get_plaintext().split()
    if len(args_list) < 2:
        await bili.finish("命令有误！")
    if args_list[1] == "add":
        follower_test = await get_follower(args_list[2])
        if follower_test:
            if is_group:
                add_res = add_uid(args_list[2], get_qq, group_list=group_id)
            else:
                add_res = add_uid(args_list[2], get_qq, qq_list=get_qq)
            if add_res:
                await bili.finish("添加成功！")
            else:
                await bili.finish("数据添加失败！")
        else:
            await bili.finish("添加失败！")
        
    elif args_list[1] == "select":
        follower_test = await get_follower(args_list[2])
        if follower_test:
            await bili.finish("查询粉丝数为：%s！" % follower_test)
        else:
            await bili.finish("查询失败！")
    elif args_list[1] == "del":
        del_res = del_uid(args_list[2], get_qq)
        if del_res:
            await bili.finish("删除uid绑定成功！")
        else:
            await bili.finish("删除uid绑定失败！")
    elif args_list[1] == "help":
        await bili.finish("<bili add b站uid> 绑定\n<bili select b站uid> 查询粉丝数")
    
    else:
        await bili.finish("未知命令！")
    
    


scheduler.add_job(main, "interval", minutes=1)