```json5
{
    "http_header": {  // 建议使用常用浏览器的ua
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36",
        "Referer": "https://www.bilibili.com/",
        "Connection": "keep-alive"
    },
    "default_vote": {  // 默认投票
        "mode": 1,  // 选择模式，1为获取案件后有观点就参考观点，没有就投默认，2为获取案件后有观点就参考观点，没有就先暂存案件id跳过，等案件池空了获取不到观点后再倒回去投默认
        "vote": [0, 1],  // 默认投票，0为好，1为普通，2为差，3为无法判断,填多个为随机投票，填一个为固定投票
        "once": true  // true为审满案件后退出，false为获取不到新案件后退出
    },
    "users": [
        {
            "cookieDatas": {  // 账号一
                "SESSDATA": "xxxxx",
                "bili_jct": "xxxxx",
                "DedeUserID": "xxxxx"
            }
        },
        {
            "cookieDatas": {  // 账号二
                "SESSDATA": "xxxxx",
                "bili_jct": "xxxxx",
                "DedeUserID": "xxxxx"
            }
        }
    ],
    "push": {  // 推送
        "enable": "false",  // 开关，false为关闭推送，true或其他任意字段为开启推送
        "msgtpye": ["CookieExpires", "UnknownError", "DailyMissions"],  // 选择推送类型，"CookieExpires"为cookie过期推送，"UnknownError"为运行报错推送，"DailyMissions"为每日任务完成状况推送
        "wxpush": {  // 企业微信推送必填，获取方法自行搜索
            "corpid": "xxxxx",  // 企业id，字符串类型
            "secret": "xxxxx",  // 应用密钥，字符串类型
            "agentid": 1000001  // 应用id，数字整型
        }
    }
}
```