# fl-fserver

## 部署服务

### 准备 linux 服务器

推荐系统：
- Ubuntu 20.04 LTS, 22.04 LTS
- Debian 11 (Bullseye), 12 (Bookworm)

### 下载代码

下载代码可以通过以下两种方式：

1. 下载 ZIP 文件：
   - 访问 https://github.com/yinheli/fl-fserver
   - 点击绿色的 "Code" 按钮
   - 选择 "Download ZIP"
   - 解压下载的文件

2. 使用 Git 克隆仓库：
   - 确保已安装 Git
   - 打开终端或命令提示符
   - 运行以下命令：
     ```bash
     git clone https://github.com/yinheli/fl-fserver.git
     ```
   - 这将在当前目录下创建一个名为 "fl-fserver" 的文件夹，包含所有代码

选择其中一种方法即可获取代码。

### 启动服务


### 启动服务

1. 进入项目目录：
   ```bash
   cd fl-fserver
   ```

2. 执行启动脚本：
   ```bash
   bash up.sh
   ```

   这个脚本会自动执行以下操作：
   - 检查并安装 Docker / Docker Compose（如果尚未安装）
   - 构建并启动所有必要的服务容器

3. 等待脚本执行完成。脚本会显示服务状态和最近的日志信息。

注意：首次运行可能需要一些时间来下载和构建镜像。

如果一切正常，你应该能看到类似以下的输出：

```
fsdownload-1  | [2024-09-25 16:11:21 +0000] [1] [INFO] Starting gunicorn 23.0.0
fsdownload-1  | [2024-09-25 16:11:21 +0000] [1] [INFO] Listening at: http://0.0.0.0:5555 (1)
fsdownload-1  | [2024-09-25 16:11:21 +0000] [1] [INFO] Using worker: sync
fsdownload-1  | [2024-09-25 16:11:21 +0000] [7] [INFO] Booting worker with pid: 7
websocket-1   | [2024-09-25T16:11:21Z INFO  websocket_server] Starting server on 0.0.0.0:8765
init-1        | Running scheduled task: delete_expired_users
init-1        | init done
```