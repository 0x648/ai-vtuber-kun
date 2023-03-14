# AI Vtuber Kun
AI Vtuber Kun是一个由OpenAI驱动的虚拟主播，可以在Bilibili直播中与观众实时互动。它使用自然语言处理和文本转语音技术生成对观众问题的回答。

### 要求
- Python 3.7或更高版本
- OpenAI API密钥
- Bilibili帐户和房间ID
- `openai`、`pyttsx3`和`bilibili-api-python` Python库
### 安装
1. 克隆存储库：
```bash
git clone https://github.com/your_username/AI-Vtuber-Kun.git
```
2. 安装所需的软件包：
```
pip install openai pyttsx3 bilibili-api-python
```
### 使用方法
1. 运行程序：
```python
python main.py
```
2. 在Bilibili上开始直播并进入您的直播间。
3. AI-Vtuber-Kun将开始实时生成对观众问题的回答并通过语音讲述。
### 给新手的 OBS 配置详解：
#### blivechat 配置
- 来源 > + > 浏览器 > 新建 > URL：填入 https://bilichat.3shain.com/bilibili/你的直播间id 即可
#### 音频配置
- 来源 > + > 应用程序音频采集 > 新建 > 选择 python
#### B 站推流配置
- 设置（Preferences）> 直播 > 服务：选 Bilibili Live ...
- 推流码填写「B 站首页 > 头像 > 推荐服务 > 直播中心 > 左侧“我的直播间”> 填好直播分类、房间标题 > 开始直播，然后会显示的串流密钥」
### 待办事项
- [ ] 实现敏感词过滤
- [ ] 添加Microsoft TTS支持
### 许可证
本项目根据Apache License 2.0许可证发布。有关详情，请参见LICENSE文件。
