📌 Twitter-DeepSeek-Feishu 自动推文翻译 & 推送系统
本项目实现了 自动获取 Twitter/X 推文、翻译成中文，并发送到飞书群聊的全流程自动化。
适用于 跟踪 Elon Musk 相关推文，并提供 定期自动推送、日志管理、失败重试 等功能。

📢 功能介绍
✅ 自动获取 Twitter/X 上 Elon Musk 相关推文
✅ 保存推文到 tweet_monitor.log（不会覆盖旧内容）
✅ 筛选最近 10 条推文，并随机选择 3 条进行翻译
✅ 使用 DeepSeek API 进行翻译（英文 → 中文）
✅ 将推文及翻译结果发送到飞书群聊
✅ **支持 180 分钟（3 小时）自动执行一次
✅ 日志记录所有推文及发送状态，确保数据可追溯

📂 代码分工
文件名	功能描述
main.py	核心控制流，负责完整的推文抓取、翻译、飞书推送
main2.py	备用控制流，与 main.py 功能类似
deepfei.py	处理 tweet_monitor.log，翻译并发送推文到飞书
deepseek.py	DeepSeek API 交互，提供翻译服务
twitter.py	负责调用 Twitter API 获取推文
userid.py	查询 Twitter 用户 ID 或飞书用户 ID
rednote.py	辅助工具，可能涉及日志解析或数据处理
rednotev0.py	旧版本的 rednote.py
tweet_backup.log	旧推文存档日志
tweet_monitor.log	监控最新推文并记录
requirements.txt	依赖包列表
🛠️ Twitter → DeepSeek → 飞书：完整工作流
该项目的核心逻辑由 main.py 控制，完整的工作流程如下：

1️⃣ 从 Twitter 获取推文
调用 Twitter API，搜索 elonmusk -is:retweet（排除转推）
写入 tweet_monitor.log，保证后续翻译 & 推送的稳定性
2️⃣ 读取最新推文
从 tweet_monitor.log 提取最近 10 条推文
随机选择 3 条 进行翻译
3️⃣ 翻译推文
使用 DeepSeek API 进行 英文 → 中文翻译
若 DeepSeek 失败，自动跳过该推文
4️⃣ 发送推文到飞书
获取 飞书 API tenant_access_token
重试 3 次 确保消息发送成功
发送到指定的飞书群聊 TARGET_CHAT_ID
5️⃣ 定时任务调度
每 180 分钟（3 小时）自动执行：
获取最新推文
更新日志
翻译
推送到飞书
🚀 运行方式
1️⃣ 安装依赖
pip install -r requirements.txt
2️⃣ 运行 main.py
python main.py
3️⃣ 查看日志
cat tweet_monitor.log  # Linux/macOS
type tweet_monitor.log  # Windows
🔑 API Key & 账户配置
⚠️ 请务必替换以下 API Key，否则程序无法运行！

1️⃣ 飞书 API
请在飞书开发者后台获取 APP_ID 和 APP_SECRET，然后替换：


APP_ID = "your_app_id_here"
APP_SECRET = "your_app_secret_here"
FEISHU_API_URL = "https://open.feishu.cn/open-apis"
TARGET_CHAT_ID = "your_chat_id_here"  # 目标群聊 ID
2️⃣ Twitter API
你需要一个 Twitter/X API Key，然后替换：


BEARER_TOKEN = "your_twitter_bearer_token_here"
client = tweepy.Client(bearer_token=BEARER_TOKEN)
3️⃣ DeepSeek API
获取 DeepSeek API Key 并替换：


DEEPSEEK_API_KEY = "your_deepseek_api_key_here"
openai.api_key = DEEPSEEK_API_KEY
openai.api_base = "https://api.deepseek.com/beta"
📌 注意事项
⚠️ tweet_monitor.log 只会追加新内容，不会删除旧数据
⚠️ 推文去重机制 仅适用于 当前运行时，重启后可能重复处理历史推文
⚠️ DeepSeek API 失败时，该推文会被跳过，不会影响其他推文
⚠️ 飞书 API 发送消息时会自动重试 3 次，确保可靠性

🔧 未来优化方向
🚀 1. 进一步优化推文去重逻辑

目前仅使用 seen_tweets 记录已处理推文，重启后数据会丢失
可以改进为基于 tweet_monitor.log 进行去重，防止重启后重复处理相同推文
🚀 2. 深入优化 DeepSeek API

目前若 DeepSeek 翻译失败，则该推文跳过
可以改进为：增加重试机制，确保推文翻译成功率更高
🚀 3. 更丰富的飞书推送

目前仅支持文本消息
可以扩展为富文本、卡片消息，提高可读性
🚀 4. 支持 Web 端可视化历史推文

当前 tweet_monitor.log 仅是文本文件
可以增加 Web 页面，展示历史推文 & 翻译内容
📅 总结
本项目提供了一整套 自动化推文获取、翻译、推送到飞书 的解决方案，适用于监控 Elon Musk 推文并进行中文翻译推送。
未来可以优化 推文去重、翻译可靠性、飞书推送格式，以及 Web 端可视化展示历史数据。

🚀 让推文翻译更自动化、更高效！


---

### **📌 主要优化**
✅ **使用 `README.md` 标准格式，适合直接复制**  
✅ **增加 API Key 替换提醒，防止运行时报错**  
✅ **提供更详细的 `运行方式`、`注意事项`，方便团队使用**  
✅ **列出 `未来优化方向`，确保项目可扩展性**  

📌 **这个 `README.md` 现在可以直接放到你的 GitHub 或项目目录中，供团队使用！** 🚀