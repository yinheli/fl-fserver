# WebSocket 通讯初步分析

这个项目缺少原始文档，参考代码，初步分析，通讯协议。


## 消息格式

所有消息均采用 JSON 格式进行传输。

### 初始化消息 (InitMessage)

客户端在连接建立后发送的第一条消息，用于初始化连接。

```json
{
    "cmd": "init",
    "token": "your_token_here"
}
```

- `cmd`: 固定为 `"init"`，表示初始化命令。
- `token`: 客户端的身份令牌，用于验证身份。

### 响应消息 (ResponseMessage)

服务器发送给客户端的响应消息。

```json
{
    "cmd": "response_command",
    "code": "response_code",
    "session_id": "optional_session_id",
    "extra": {
        "key1": "value1",
        "key2": "value2"
    }
}
```

- `cmd`: 响应的命令。
- `code`: 响应的状态码。
- `session_id`: 可选的会话 ID。
- `extra`: 额外的键值对数据。

### 心跳消息 (Heartbeat)

服务器定期发送的心跳消息，确保连接保持活跃。

```json
{
    "cmd": "Heartbeat",
    "code": "1",
    "extra": {}
}
```

- `cmd`: 固定为 `"Heartbeat"`，表示心跳命令。
- `code`: 固定为 `"1"`，表示心跳状态。
- `extra`: 额外数据，通常为空。

### 检查设备消息 (checkDevice)

客户端发送的检查设备消息，服务器返回当前房间的客户端数量。

客户端请求：

```json
{
    "cmd": "checkDevice"
}
```

服务器响应：

```json
{
    "cmd": "checkDevice",
    "code": "1",
    "extra": {}
}
```

- `cmd`: 固定为 `"checkDevice"`，表示检查设备命令。
- `code`: `"1"` 表示有多个客户端，`"0"` 表示只有一个客户端。
- `extra`: 额外数据，通常为空。

### 执行命令消息 (execute)

客户端发送的执行命令消息，服务器处理后不返回响应。

```json
{
    "cmd": "execute",
    "extra": {
        "command": "your_command_here"
    }
}
```

- `cmd`: 固定为 `"execute"`，表示执行命令。
- `extra`: 包含执行命令的具体内容。

### 执行结果消息 (execute_result)

客户端发送的执行结果消息，服务器处理后不返回响应。

```json
{
    "cmd": "execute_result",
    "extra": {
        "data": "result_data_here"
    }
}
```

- `cmd`: 固定为 `"execute_result"`，表示执行结果命令。
- `extra`: 包含执行结果的具体数据。

## 通讯流程

1. **连接建立**：客户端与服务器建立 WebSocket 连接。
2. **初始化连接**：客户端发送初始化消息 (`InitMessage`)。
3. **身份验证**：服务器验证客户端身份，返回响应消息 (`ResponseMessage`)。
4. **心跳检测**：服务器定期发送心跳消息 (`Heartbeat`) 以保持连接活跃。
5. **消息处理**：客户端和服务器根据具体命令进行消息处理，包括检查设备 (`checkDevice`)、执行命令 (`execute`) 和执行结果 (`execute_result`) 等。
6. **连接关闭**：客户端或服务器关闭连接，服务器清理相关资源。

## 错误处理

- 如果初始化消息中的令牌无效，服务器将返回错误响应并关闭连接。
- 如果在处理消息时发生错误，服务器将记录错误日志并尝试继续处理其他消息。
- 如果连接断开，服务器将清理相关资源并移除客户端。

## 日志记录

服务器使用 `log` 库记录以下类型的日志：

- `info`：记录正常的操作信息，如连接建立、消息发送和接收等。
- `warn`：记录警告信息，如心跳消息发送失败等。
- `error`：记录错误信息，如消息处理失败、连接断开等。
