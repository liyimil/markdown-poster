# S01 Agent 循环详解笔记

> 基于 `agents/s01_agent_loop.py` 源码逐行分析，配合 `docs/zh/s01-the-agent-loop.md` 设计思路。

---

## 一、问题：模型能推理，但碰不到真实世界

你问 ChatGPT "我桌面上有哪些文件？"——它不知道。它没有眼睛，没有手，跑不出你的电脑。

传统的聊天机器人只能**说话**。你说一句，它回一句。如果你想让它帮你"列出当前目录的 Python 文件"，你得自己跑 `ls *.py`，把结果粘贴给它，它再基于结果给你建议。**你自己就是那个循环**——反复在终端和聊天框之间切换。

s01 要解决的就是这个：**让模型能操作真实世界。** 不是"建议你跑什么命令"，而是它**自己跑**命令，看到结果，再决定下一步。

---

## 二、解决方案：一个 while 循环 + 一个 bash 工具

核心代码不到 30 行：

```python
def agent_loop(messages):
    while True:
        response = client.messages.create(
            model=MODEL, system=SYSTEM, messages=messages,
            tools=TOOLS, max_tokens=8000,
        )
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            return
        results = []
        for block in response.content:
            if block.type == "tool_use":
                output = run_bash(block.input["command"])
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })
        messages.append({"role": "user", "content": results})
```

这就是整个 agent。后面 11 章都在这个循环上叠加机制——循环本身始终不变。

数据流向：

```
User: "列出 Python 文件"
    ↓
messages = [{"role": "user", "content": "列出 Python 文件"}]
    ↓
[LLM call] → response.stop_reason = "tool_use"
              response.content = [{"type": "tool_use", "name": "bash",
                                   "input": {"command": "ls *.py"}}]
    ↓
messages.append(assistant response)   # 模型说"我要跑 ls *.py"
    ↓
run_bash("ls *.py") → "hello.py\nmain.py"
    ↓
messages.append({"role": "user", "content": [{"type": "tool_result",
                  "tool_use_id": "...", "content": "hello.py\nmain.py"}]})
    ↓
[LLM call] → response.stop_reason = "end_turn"
              response.content = [{"type": "text", "text": "当前目录有2个Python文件..."}]
    ↓
stop_reason != "tool_use" → return（循环结束）
```

**初学者关键理解**：模型不是"想要"跑命令，而是通过 API 的 `stop_reason` 字段告诉你"我需要调用工具"。你的代码执行了工具，把结果作为"用户消息"追加回去。模型看到结果后决定：继续调工具，还是回复文本。**你（Harness）是模型的手，模型是你的脑。**

---

## 三、s01 之前 vs 之后

| 组件 | 之前（纯 LLM chat） | s01 |
|------|---------------------|-----|
| Agent loop | 无（你自己手动循环） | `while stop_reason == "tool_use"` |
| 工具 | 无 | `bash`（1个工具） |
| 消息管理 | 你自己复制粘贴 | `messages` 列表自动累积 |
| 控制流 | 你决定下一步 | `stop_reason` 决定 |

---

## 四、源码逐行分析

### 4.1 环境初始化

```python
load_dotenv(override=True)
```

`override=True` 的含义：如果 `.env` 文件和系统环境变量有同名项，`.env` 的优先。这确保了开发配置的隔离——不管你的系统环境变量怎么设，项目 `.env` 说了算。

```python
if os.getenv("ANTHROPIC_BASE_URL"):
    os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)
```

这段处理了一个 SDK 行为冲突：当设置了 `ANTHROPIC_BASE_URL`（自定义 API 代理，如 OpenRouter、DeepSeek 网关）时，你想用的是 API Key 认证。但 Anthropic SDK 检测到 `ANTHROPIC_AUTH_TOKEN` 会优先走 OAuth 认证——两者互斥。所以这里直接删掉 `ANTHROPIC_AUTH_TOKEN`，确保走 API Key 路径。

```python
client = Anthropic(base_url=os.getenv("ANTHROPIC_BASE_URL"))
MODEL = os.environ["MODEL_ID"]
```

`base_url` 为 `None` 时 SDK 用默认的 `https://api.anthropic.com`。注意 `MODEL` 用 `os.environ["MODEL_ID"]`（方括号）而非 `os.getenv("MODEL_ID")`——前者在变量不存在时抛出 `KeyError`，快速失败。这比静默地用 `None` 然后 API 调用时报一个莫名其妙的错误好得多。

### 4.2 System Prompt

```python
SYSTEM = f"You are a coding agent at {os.getcwd()}. Use bash to solve tasks. Act, don't explain."
```

"Act, don't explain" 是这个系列的核心理念。模型默认倾向于"解释我要做什么"，但 agent 需要的是"直接做"。

`{os.getcwd()}` 动态注入工作目录——让模型知道自己的"身体"在哪里。如果不告诉它，它可能会假设自己在 `/` 或某个随机位置。

### 4.3 工具定义

```python
TOOLS = [{
    "name": "bash",
    "description": "Run a shell command.",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {"type": "string"}
        },
        "required": ["command"],
    },
}]
```

这是 Anthropic API 的 tool use 格式。三个关键字段：
- **`name`**：模型在 tool_use block 中引用的名字
- **`description`**：帮助模型判断"什么时候该用这个工具"
- **`input_schema`**：JSON Schema 格式的参数定义。模型必须按这个 schema 填充参数

为什么是 JSON Schema？因为 Anthropic 的模型在训练时见过大量 JSON Schema，它天然理解"这个工具需要什么参数、每个参数是什么类型"。这和 function calling 的哲学一致——用结构化契约代替自然语言描述。

### 4.4 `run_bash()` — 执行命令

```python
def run_bash(command: str) -> str:
    dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(d in command for d in dangerous):
        return "Error: Dangerous command blocked"
```

**`any(d in command for d in dangerous)`** 是一个生成器表达式——遍历 `dangerous` 列表，检查每个危险模式是否**作为子串**出现在命令中。任一匹配则返回 True。注意这是子串匹配，不是精确匹配——`"sudo rm file"` 会被拦截，因为包含 `"sudo"`。

```python
    r = subprocess.run(
        command, shell=True, cwd=os.getcwd(),
        capture_output=True, text=True, timeout=120
    )
```

**初学者**：`subprocess.run` 是 Python 执行外部命令的标准方式。参数解析：
- **`shell=True`**：通过 shell 解释器执行，支持管道（`|`）、重定向（`>`）、通配符（`*`）等 shell 语法。代价是安全风险——如果命令字符串包含用户输入，可能被注入恶意代码
- **`cwd=os.getcwd()`**：命令在当前工作目录执行，与 agent 上下文一致
- **`capture_output=True`**：同时捕获 stdout 和 stderr
- **`text=True`**：输出是字符串而非 bytes
- **`timeout=120`**：2 分钟超时，防止命令卡死

```python
    out = (r.stdout + r.stderr).strip()
    return out[:50000] if out else "(no output)"
```

stdout 和 stderr 合并——模型需要同时看到正常输出和错误信息。`[:50000]` 截断防止输出撑爆上下文窗口。这个数字在 s06 被抽象为可配置的常量，但原理不变。

异常处理三条路径：
- `TimeoutExpired`：命令跑了 120 秒还没结束，强制终止
- `FileNotFoundError`：命令不存在（如拼写错误）
- `OSError`：操作系统级错误（权限不足、磁盘满等）。注意这在 s01 原始代码中没有，但后来在 PR #159 中被加入——生产环境的边界条件处理是逐步完善的

### 4.5 `agent_loop()` — 核心循环

```python
def agent_loop(messages: list):
    while True:
        response = client.messages.create(
            model=MODEL, system=SYSTEM, messages=messages,
            tools=TOOLS, max_tokens=8000,
        )
```

每轮把**完整的**对话历史发给模型。注意 `system` 参数——它不在 `messages` 列表里，而是单独的字段。这是因为 Anthropic API 把 system prompt 视为特殊角色，不参与 user/assistant 的交替模式。

**`messages` 的结构**（初学者重要）：

在 Anthropic API 中，messages 是一个列表，交替存放 user 和 assistant 消息：

```python
[
    {"role": "user", "content": "列出 Python 文件"},          # 用户输入
    {"role": "assistant", "content": [ContentBlock(...)]},    # 模型回复（含 tool_use）
    {"role": "user", "content": [{"type": "tool_result", ...}]},  # 工具结果
    {"role": "assistant", "content": [ContentBlock(...)]},    # 模型最终回复
]
```

**`response.content`** 是一个 `ContentBlock` 对象列表。每个 block 可以是：
- `TextBlock`：`{"type": "text", "text": "我帮你列出了文件..."}`
- `ToolUseBlock`：`{"type": "tool_use", "id": "toolu_xxx", "name": "bash", "input": {"command": "ls"}}`

`block.id` 是 API 自动生成的唯一标识（如 `"toolu_01ABC123..."`），用于把 tool_result 关联回对应的 tool_use。

```python
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            return
```

这条判断是循环的唯一出口。`stop_reason` 有几种可能值：
- `"tool_use"`：模型想调用工具 → 执行工具，继续循环
- `"end_turn"`：模型正常结束 → 退出循环
- `"max_tokens"`：达到 `max_tokens` 上限 → 非正常退出
- `"stop_sequence"`：命中自定义停止序列

**为什么先 append 再判断？** 因为即使模型不再调工具，它的最终回复（文本回答）也需要被保存到 messages 中。调用方（REPL）从 `messages[-1]["content"]` 提取最终回复。

```python
        results = []
        for block in response.content:
            if block.type == "tool_use":
                output = run_bash(block.input["command"])
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })
        messages.append({"role": "user", "content": results})
```

遍历所有 content block，只处理 `tool_use` 类型。注意 `tool_use_id` 的配对——如果错配，模型会困惑"这个结果是哪个命令的输出？"。

**tool_result 的 role 是 "user"**——这是 Anthropic API 的设计：工具结果被视为"用户提供的信息"。在对话轮次上，模式是 `user → assistant（含 tool_use） → user（含 tool_result） → assistant → ...`。这保持了严格的交替结构。

### 4.6 REPL 入口

```python
if __name__ == "__main__":
    history = []
    while True:
        query = input("\033[36ms01 >> \033[0m")
        if query.strip().lower() in ("q", "exit", ""):
            break
        history.append({"role": "user", "content": query})
        agent_loop(history)
        response_content = history[-1]["content"]
        if isinstance(response_content, list):
            for block in response_content:
                if hasattr(block, "text"):
                    print(block.text)
```

**`\033[36m`** 是 ANSI 转义码——`\033` 是 ESC 字符（八进制 33），`[36m` 设置文字颜色为青色。`\033[0m` 重置所有样式。这和 HTML 的 `<span style="color:cyan">` 是同一个概念，只是在终端里用控制字符实现。

`history` 跨多轮用户输入持久化——你第一次说"创建 hello.py"，第二次说"给它加个 main 函数"，agent 记得 hello.py 已经存在。每次用户输入都是一次新的 `agent_loop(history)` 调用。

提取最终回复时遍历 `response.content`，只打印 `text` 类型的 block。`hasattr(block, "text")` 是类型检查——`TextBlock` 有 `text` 属性，`ToolUseBlock` 没有。跳过 tool_use block 避免给用户看"我调用了 ls 命令"的内部细节。

---

## 五、完整流程走读

**场景**：用户输入 "列出当前目录的 Python 文件"。

### 第 1 轮

1. `history = [{"role": "user", "content": "列出当前目录的 Python 文件"}]`
2. `agent_loop(history)` 启动
3. API 调用：`client.messages.create(model=..., messages=history, tools=TOOLS, ...)`
4. 模型返回：`stop_reason = "tool_use"`，`content = [ToolUseBlock(name="bash", input={"command": "ls *.py"})]`
5. `history.append({"role": "assistant", "content": [ToolUseBlock]})`
6. 遍历 content blocks → 找到 tool_use → 执行 `run_bash("ls *.py")`
7. 结果：`"hello.py\nmain.py"`
8. `history.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": "toolu_xxx", "content": "hello.py\nmain.py"}]})`

### 第 2 轮

1. API 调用：messages 现在包含 3 条消息（user 问题 + assistant tool_use + user tool_result）
2. 模型看到 `hello.py` 和 `main.py`，决定任务完成
3. 返回：`stop_reason = "end_turn"`，`content = [TextBlock(text="当前目录有2个Python文件：hello.py 和 main.py")]`
4. `history.append({"role": "assistant", "content": [TextBlock]})`
5. `stop_reason != "tool_use"` → 退出循环
6. REPL 提取 `history[-1]["content"]` → 打印 "当前目录有2个Python文件：hello.py 和 main.py"

**关键观察**：模型在第一轮决定"我需要先拿到文件列表"，它不直接回答——因为**它知道自己不知道**。工具结果补上了这个信息缺口，第二轮它就能回答了。

---

## 六、设计洞察

### 6.1 Agent 的本质 = 循环 + 工具 + 记忆

`agent_loop = while + tools + messages`。`while` 提供持续行动能力，`tools` 提供执行能力，`messages` 提供记忆能力。拆开来看都不复杂，但组合在一起就产生了**模型与环境之间的闭环**——模型行动 → 观察结果 → 调整行动 → 再观察。这是所有 agent 的共同骨架，从 s01 到 s12 到 Claude Code 生产版。

### 6.2 Harness 层：结构 vs 智能的边界

LLM 提供**推理和决策**（"我需要跑 ls 命令来看看有哪些 Python 文件"），Harness 提供**结构和约束**（while 循环、消息格式、工具执行、超时控制）。这个分工贯穿整个系列。模型是"脑"，Harness 是"身体"——脑决定做什么，身体负责执行和提供反馈。

### 6.3 对话历史的累积

每次 API 调用都发送**完整的** messages 列表，不是增量。这意味着第 10 轮调用时，前 9 轮的所有交互都在 context 里。好处是模型拥有完整的"记忆"，代价是 token 消耗线性增长。s06 的压缩机制就是解决这个代价的。

### 6.4 API 设计的影响

Anthropic 的 Messages API 不是被设计来"聊天"的——它被设计来支持 agent。`stop_reason`、`tool_use` block、`tool_result` role——这些抽象本身就是为"模型调用工具 → 收到结果 → 继续推理"这个循环而生的。s01 的 30 行代码之所以能工作，是因为 API 层已经为这种模式做好了设计。
