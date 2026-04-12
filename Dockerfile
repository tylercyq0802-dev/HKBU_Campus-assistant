# ---------------------------------------------------
# 阶段一：厨房 (Builder Stage)
# 任务：准备环境，安装所有的 Python 依赖包
# ---------------------------------------------------
# 我们选择基于 Debian 的 Python 3.11 slim 版本，体积小巧且兼容性好
FROM python:3.11-slim AS builder

# 设置工作目录，相当于我们在集装箱里划出了一块叫 /app 的工作区
WORKDIR /app

# 【优化点】经过确认 requirements.txt 中使用了 psycopg2-binary 等预编译包（预制菜），
# 因此我们完全去除了 gcc 等沉重的系统编译工具，让构建速度起飞！

# 把依赖清单带进“厨房”
COPY requirements.txt .

# 把依赖包安装到专门的目录（--user 模式），这样方便下一阶段直接整个端走
# --no-cache-dir 可以防止缓存占用空间
RUN pip install --user --no-cache-dir -r requirements.txt


# ---------------------------------------------------
# 阶段二：餐桌/便当盒 (Production Stage)
# 任务：只带上必需的代码和装好的包，轻装上阵
# ---------------------------------------------------
FROM python:3.11-slim

WORKDIR /app

# 【关键点】从“厨房” (builder 阶段) 把做好的“菜”（安装好的第三方依赖包）直接复制过来
COPY --from=builder /root/.local /root/.local

# 把我们的核心业务代码放进集装箱
# 注意：我们不需要拷贝 venv、.env 等文件，一会儿我们会用 .dockerignore 排除它们
COPY ChatGPT_HKBU.py config(cleaned).ini db.py main.py ./

# 告诉系统去哪里找刚才装好的第三方包
ENV PATH=/root/.local/bin:$PATH

# 设置时区为香港时间（可选项，对定时任务很友好）
ENV TZ=Asia/Hong_Kong

# 集装箱通电后，自动执行的启动口令
CMD ["python", "main.py"]