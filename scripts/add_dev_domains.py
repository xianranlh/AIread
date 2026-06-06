"""追加 MySQL / Linux / Git 三个开发常用领域到 quiz_seed.json（含「调优/排查」章节）。
按 (domain, question) 去重，answer_md 为要点式 Markdown。幂等可重复执行。"""
import json
from pathlib import Path

SEED = Path(__file__).resolve().parent.parent / "app" / "quiz_seed.json"

NEW = [
# ===================== MySQL =====================
{"domain": "mysql", "section": "索引", "ord": 0, "category": "基础",
 "question": "MySQL 为什么用 B+ 树做索引？和 B 树、哈希、跳表有何区别？",
 "answer_md": "- **B+ 树**：数据全放叶子节点，非叶子只存索引 → 单节点能放更多 key，**树更矮**（3-4 层存千万级），磁盘 IO 次数少\n- 叶子节点用**双向链表**串联 → 天然支持**范围查询**和排序（order by/between）\n- vs **B 树**：B 树每个节点都存数据，单节点 key 少、树更高；范围查询要回溯\n- vs **哈希索引**：哈希 O(1) 等值查询快，但**不支持范围/排序/最左前缀**，且有哈希冲突；Memory 引擎用\n- vs **跳表**（Redis ZSet 用）：实现简单、范围也行，但同样数据下层数比 B+ 树高，磁盘场景 IO 多\n- 结论：磁盘存储 + 既要等值又要范围 → B+ 树最优"},
{"domain": "mysql", "section": "索引", "ord": 1, "category": "基础",
 "question": "聚簇索引与非聚簇索引的区别？什么是回表和覆盖索引？",
 "answer_md": "- **聚簇索引（主键索引）**：叶子节点直接存**整行数据**，InnoDB 表数据就是按主键组织的 B+ 树（一张表只有一个）\n- **非聚簇索引（二级索引）**：叶子节点存的是**主键值**，不是整行\n- **回表**：用二级索引查到主键，再拿主键去聚簇索引查整行——**两次 B+ 树查找**\n- **覆盖索引**：要查的列都在二级索引里（索引覆盖了 select 字段）→ 不用回表，explain 显示 `Using index`\n- 实践：高频查询用**联合索引覆盖**避免回表；主键建议用自增（顺序写、避免页分裂），别用 UUID（随机插入导致页分裂、索引膨胀）"},
{"domain": "mysql", "section": "索引", "ord": 2, "category": "基础",
 "question": "联合索引的最左前缀原则？哪些情况会导致索引失效？",
 "answer_md": "- **最左前缀**：联合索引 (a,b,c) 相当于建了 (a)、(a,b)、(a,b,c)；查询必须从最左列开始连续匹配才能用上\n- 索引失效常见场景：\n  - 违反最左前缀（只查 b 或 c）\n  - 在索引列上做**运算/函数/类型转换**：`WHERE YEAR(t)=2024`、字符串列传数字（隐式转换）\n  - 用 `!=`、`NOT IN`、`<>`、`IS NOT NULL`（视情况）\n  - `LIKE '%xx'` 前导通配符\n  - `OR` 连接的列有未建索引的\n  - 范围查询右边的列：(a,b,c) 中 a 用了范围（>、<、between），b、c 索引中断\n- 排查靠 `EXPLAIN` 看 key / type / Extra"},
{"domain": "mysql", "section": "事务与锁", "ord": 3, "category": "基础",
 "question": "事务的 ACID 与四种隔离级别分别解决什么问题？",
 "answer_md": "- **ACID**：原子性（undo log 回滚）、一致性（目的）、隔离性（锁 + MVCC）、持久性（redo log）\n- 并发问题：**脏读**（读到未提交）、**不可重复读**（两次读同行值不同）、**幻读**（两次读行数不同）\n- 四种隔离级别：\n  | 级别 | 脏读 | 不可重复读 | 幻读 |\n  |---|---|---|---|\n  | 读未提交 RU | ✓ | ✓ | ✓ |\n  | 读已提交 RC | ✗ | ✓ | ✓ |\n  | 可重复读 RR（MySQL 默认）| ✗ | ✗ | ✓(InnoDB 用间隙锁基本解决) |\n  | 串行化 | ✗ | ✗ | ✗ |\n- InnoDB 的 RR 通过 **MVCC + 间隙锁**，在多数场景下也避免了幻读"},
{"domain": "mysql", "section": "事务与锁", "ord": 4, "category": "进阶",
 "question": "MVCC 的实现原理？undo log 和 ReadView 怎么配合？",
 "answer_md": "- **MVCC（多版本并发控制）**：读不加锁、读写不冲突，提升并发\n- 每行隐藏字段：`DB_TRX_ID`（最后修改的事务 id）、`DB_ROLL_PTR`（指向 undo log 的回滚指针）\n- **undo log 版本链**：每次修改生成一个旧版本，用回滚指针串成链\n- **ReadView**：快照读时生成，含活跃事务列表（m_ids）、min_trx_id、max_trx_id、creator_trx_id\n- 可见性判断：沿版本链找第一个对当前 ReadView 可见的版本（该版本 trx_id 已提交且不在活跃列表中）\n- **RC 与 RR 区别**：RC 每次 select 都生成新 ReadView（所以不可重复读）；RR 只在**第一次** select 生成、整个事务复用（所以可重复读）\n- 注意：**当前读**（select...for update / update / delete）读最新版本并加锁，不走 MVCC 快照"},
{"domain": "mysql", "section": "事务与锁", "ord": 5, "category": "进阶",
 "question": "MySQL 有哪些锁？间隙锁、临键锁是什么？如何避免死锁？",
 "answer_md": "- 粒度：**表锁 / 行锁**（InnoDB 支持行锁）；模式：共享锁 S / 排他锁 X\n- 行锁三种算法（RR 级别）：\n  - **Record Lock**：锁单条索引记录\n  - **Gap Lock 间隙锁**：锁记录之间的间隙，防止插入 → 解决幻读\n  - **Next-Key Lock 临键锁**：Record + Gap，左开右闭区间，InnoDB 默认\n- 行锁**加在索引上**：查询没走索引 → 退化为表锁\n- 死锁避免：\n  - 多事务按**相同顺序**访问资源/加锁\n  - 事务尽量短小、一次锁定所需全部资源\n  - 降低隔离级别（RC 无间隙锁）、加合适索引避免锁范围扩大\n  - InnoDB 有死锁检测（自动回滚代价小的事务），`show engine innodb status` 看死锁日志"},
{"domain": "mysql", "section": "事务与锁", "ord": 6, "category": "进阶",
 "question": "redo log、undo log、binlog 的作用与区别？两阶段提交是什么？",
 "answer_md": "- **undo log**（InnoDB）：记录数据**修改前**的值 → 事务回滚 + MVCC 版本链\n- **redo log**（InnoDB）：物理日志，记录页的修改 → **崩溃恢复**（crash-safe），WAL 先写日志再刷盘；循环写、固定大小\n- **binlog**（Server 层）：逻辑日志，记录所有写操作 → **主从复制 + 数据恢复**；追加写、可归档\n- **两阶段提交（2PC）**：保证 redo log 与 binlog 一致——\n  1. 写 redo log，置 **prepare** 状态\n  2. 写 binlog\n  3. 提交事务，redo log 置 **commit**\n- 崩溃恢复时：redo 已 commit → 提交；redo 是 prepare 但 binlog 完整 → 提交；否则回滚。避免主库与从库数据不一致"},
{"domain": "mysql", "section": "性能调优", "ord": 7, "category": "场景设计",
 "question": "一条慢 SQL 如何排查与优化？EXPLAIN 关键字段怎么看？",
 "answer_md": "排查步骤：\n1. **定位**：开 `slow_query_log`（long_query_time），用 mysqldumpslow / pt-query-digest 找 Top SQL\n2. **EXPLAIN 分析**，重点字段：\n   - **type**：访问类型，性能 `system > const > eq_ref > ref > range > index > ALL`；出现 **ALL（全表扫描）** 要警惕\n   - **key**：实际用的索引；**key_len**：用了索引的几个列\n   - **rows**：预估扫描行数，越小越好\n   - **Extra**：`Using index`（覆盖索引，好）、`Using filesort`（额外排序，差）、`Using temporary`（临时表，差）\n3. **优化手段**：加/调联合索引（覆盖、最左前缀）、改写 SQL（避免函数、子查询改 join）、减少回表、分页优化、必要时拆分大事务\n4. 配合 `profiling` / `optimizer_trace` 看耗时分布"},
{"domain": "mysql", "section": "性能调优", "ord": 8, "category": "场景设计",
 "question": "深分页 limit 100000,10 很慢怎么优化？",
 "answer_md": "- 慢的原因：`LIMIT 100000,10` 要**扫描并丢弃前 10 万行**（回表 10 万次）才取 10 行\n- 优化方案：\n  - **延迟关联/覆盖索引**：先用覆盖索引查出 10 行的主键，再 join 回表\n    ```sql\n    SELECT * FROM t JOIN (SELECT id FROM t ORDER BY id LIMIT 100000,10) x USING(id);\n    ```\n  - **游标/书签翻页（推荐）**：记住上一页最后一个 id，`WHERE id > last_id ORDER BY id LIMIT 10`——O(1) 定位，适合无限滚动\n  - 业务上限制可翻页数 / 跳页用搜索引擎（ES）\n- 根因：避免「偏移量扫描」，改成「范围定位」"},
{"domain": "mysql", "section": "性能调优", "ord": 9, "category": "场景设计",
 "question": "分库分表有哪些方案？会带来什么问题？什么时候才需要？",
 "answer_md": "- 何时需要：**单表数据量过大**（千万~亿级、B+ 树层数增加）或**写入量超单库瓶颈**；优先考虑「先优化索引/读写分离/加缓存/归档冷数据」，分表是最后手段\n- 拆分方式：\n  - **垂直拆分**：按业务拆库、按字段拆表（大字段分离）\n  - **水平拆分**：按 range（时间/id 段）或 **hash（取模/一致性哈希）** 把数据散到多表多库\n- 带来的问题：\n  - **分布式 ID**（不能用自增）→ 雪花算法/号段\n  - **跨库 join / 聚合 / 分页**变难（需应用层合并或冗余宽表）\n  - **分布式事务**（最终一致性、TCC、本地消息表）\n  - 扩容数据迁移、跨片查询\n- 中间件：ShardingSphere、MyCat；能不拆就不拆"},
# ===================== Linux =====================
{"domain": "linux", "section": "命令与文本处理", "ord": 0, "category": "基础",
 "question": "find、grep、awk、sed 各自擅长什么？如何配合用？",
 "answer_md": "- **find** 找文件：`find /var -name '*.log' -mtime +7 -size +100M -delete`（按名/时间/大小/类型，可 -exec）\n- **grep** 按内容过滤行：`grep -rn 'ERROR' .`（-r 递归 -n 行号 -i 忽略大小写 -v 反选 -E 正则 -A/-B 上下文）\n- **sed** 流式编辑（替换/删除行）：`sed -i 's/old/new/g' f`、`sed -n '10,20p'`\n- **awk** 按列处理与统计：`awk '{print $1}'`、`awk -F: '{sum+=$3} END{print sum}'`\n- 配合示例：统计 nginx 访问 Top10 IP\n  ```bash\n  awk '{print $1}' access.log | sort | uniq -c | sort -rn | head\n  ```\n- 口诀：find 找文件、grep 找行、sed 改文本、awk 切列统计"},
{"domain": "linux", "section": "命令与文本处理", "ord": 1, "category": "基础",
 "question": "线上日志怎么排查？大日志文件如何高效定位问题？",
 "answer_md": "- **实时跟踪**：`tail -f app.log` / `tail -f | grep -i error`\n- **大文件别 cat**：用 `less`（支持 /搜索、G 到末尾）、`grep -n` 定位行、`sed -n '1000,1100p'` 看指定区间\n- **按时间/关键字过滤**：`grep '2024-06-06 14:' app.log`、`grep -A20 'Exception' app.log`（看异常栈）\n- **统计**：`grep -c ERROR`（计数）、`awk` 按接口/状态码聚合、`sort|uniq -c|sort -rn` 找高频\n- **多文件/压缩包**：`zgrep` 直接搜 .gz；`journalctl -u svc --since '10 min ago'` 看 systemd 日志\n- 排查思路：先定位时间点 → 抓关键字（error/exception/timeout）→ 看上下文栈 → 关联 trace_id 串起调用链"},
{"domain": "linux", "section": "命令与文本处理", "ord": 2, "category": "基础",
 "question": "Linux 文件权限怎么理解？chmod 755、chown 是什么意思？",
 "answer_md": "- 权限位 `rwxr-xr-x`：分**属主 u / 属组 g / 其他 o** 三组，每组 读r=4 写w=2 执行x=1\n- **chmod 755** = u=7(rwx) g=5(r-x) o=5(r-x)；常见 644（文件）、755（目录/脚本）、600（私钥）\n- 符号式：`chmod u+x f`、`chmod -R g-w dir`\n- **chown** 改属主属组：`chown user:group f`、`chown -R www:www /var/www`\n- 目录的 x 权限 = 能否进入（cd）；只有 r 没有 x 的目录能 ls 名字但访问不了内容\n- 特殊位：setuid（以属主身份执行，如 passwd）、setgid、**粘滞位 t**（/tmp，只能删自己的文件）"},
{"domain": "linux", "section": "进程与系统", "ord": 3, "category": "基础",
 "question": "怎么查看进程和端口占用？kill 的常用信号有哪些？",
 "answer_md": "- 看进程：`ps -ef | grep java`、`ps aux`、`top`/`htop`（实时）、`pgrep -f keyword`\n- 看端口：`ss -ltnp`（推荐，看监听端口+PID）、`netstat -tlnp`、`lsof -i:8080`（哪个进程占用 8080）\n- 进程树：`pstree -p`\n- **kill 信号**：\n  - `kill -15`（SIGTERM，默认）：**优雅关闭**，进程可捕获做清理\n  - `kill -9`（SIGKILL）：**强制杀死**，不可捕获，最后手段（可能丢数据）\n  - `kill -2`（SIGINT，相当于 Ctrl+C）、`kill -1`（SIGHUP，常用于重载配置）\n- 批量：`pkill -f name`、`kill $(pgrep -f xxx)`"},
{"domain": "linux", "section": "进程与系统", "ord": 4, "category": "基础",
 "question": "软链接和硬链接的区别？",
 "answer_md": "- **硬链接**（`ln src link`）：指向同一个 **inode**，是同一份数据的多个名字\n  - 删除任一不影响数据（inode 引用计数减到 0 才真正释放）\n  - **不能跨文件系统**、不能链接目录\n- **软链接/符号链接**（`ln -s src link`）：是一个**独立文件**，内容是目标路径（类似快捷方式）\n  - 有自己的 inode；**可跨文件系统、可链接目录**\n  - 源文件删除后软链接**失效**（悬空）\n- 看 inode：`ls -i`；看链接数：`ls -l` 第二列\n- 实践：部署常用软链接做版本切换（current → release_v2）"},
{"domain": "linux", "section": "进程与系统", "ord": 5, "category": "进阶",
 "question": "前台/后台/守护进程的区别？nohup、&、systemd 怎么用？",
 "answer_md": "- `cmd &`：放**后台**运行，但仍属于当前 shell 会话，**终端关闭会收到 SIGHUP 而退出**\n- `nohup cmd &`：忽略 SIGHUP，终端关了也不退；输出重定向到 nohup.out\n- `jobs` 看后台任务、`fg`/`bg` 切换、`Ctrl+Z` 挂起\n- **守护进程（daemon）**：脱离终端、后台长期运行（脱离会话、重定向标准流）\n- 生产推荐用 **systemd** 管理服务：\n  - 写 unit 文件，`systemctl start/stop/status/enable svc`\n  - 自带**开机自启、崩溃自动重启（Restart=always）、日志（journalctl）、资源限制**\n- 容器场景：进程作为 PID 1 前台运行，由容器编排（Docker/K8s）负责重启"},
{"domain": "linux", "section": "性能排查与调优", "ord": 6, "category": "场景设计",
 "question": "系统负载高怎么排查？load average 是什么含义？",
 "answer_md": "- `uptime` / `top` 看 **load average**：过去 1/5/15 分钟**平均活跃（运行+不可中断D状态）进程数**\n- 判断：load 与 **CPU 核数** 比较——4 核 load=4 满载，load 持续 > 核数说明排队\n- 三个值看趋势：1 分钟 >> 15 分钟 = 负载正在飙升；反之在回落\n- 排查路径：\n  1. `top` 看是 CPU 密集（%us 高）还是 IO 等待（**%wa 高**，可能磁盘瓶颈）还是 %sy 高（系统调用/上下文切换）\n  2. `top` 找占用高的进程 → 线程 `top -Hp <pid>`\n  3. CPU 高：看是哪段代码（Java 用 jstack 抓线程栈、arthas）\n  4. **load 高但 CPU 不高** → 大量 D 状态进程，多半是**磁盘 IO 或 NFS 阻塞**，查 `iostat`\n- 口诀：先分清 CPU 型 / IO 型 / 锁等待型，再对症"},
{"domain": "linux", "section": "性能排查与调优", "ord": 7, "category": "场景设计",
 "question": "CPU、内存、磁盘 IO、网络瓶颈分别用什么命令定位？",
 "answer_md": "- **CPU**：`top`/`htop`（%us 用户 %sy 内核 %wa IO等待 %si 软中断）、`mpstat -P ALL` 看各核、`pidstat -u` 按进程、`vmstat 1` 看 r 队列与 cs 上下文切换\n- **内存**：`free -h`（关注 available 而非 free，buff/cache 可回收）、`vmstat` 看 si/so（**换页**说明内存吃紧）、`top` 按 RES 排序、`pidstat -r`\n- **磁盘 IO**：`iostat -x 1`（**%util 接近 100% 说明磁盘忙**，await 高=响应慢）、`iotop` 按进程、`df -h`/`du -sh` 看空间\n- **网络**：`ss -s`/`ss -tn` 连接状态、`iftop`/`nethogs` 看流量与进程、`ping`/`mtr` 看延迟丢包、`tcpdump` 抓包\n- 综合面板：`dstat`、`sar`（历史数据）；Brendan Gregg 的 **USE 方法**（Utilization/Saturation/Errors 逐项过）"},
{"domain": "linux", "section": "性能排查与调优", "ord": 8, "category": "场景设计",
 "question": "内存不足怎么分析？swap、OOM Killer 是什么？",
 "answer_md": "- 先 `free -h`：**available** 才是真正可用（free + 可回收的 buff/cache）；free 小不代表内存不够\n- **swap（交换分区）**：内存不足时把不活跃页换到磁盘；`si/so`（vmstat）频繁说明在**频繁换页**，性能急剧下降\n  - 服务器常调小 `vm.swappiness`（如 10）减少换出；数据库机器有时干脆关 swap 保证延迟\n- **OOM Killer**：物理内存+swap 都耗尽时，内核按 `oom_score` 杀掉占用大/优先级低的进程\n  - 查证据：`dmesg | grep -i oom` 或 `/var/log/messages`，会看到 Out of memory: Killed process 字样\n  - 可调 `oom_score_adj` 保护关键进程\n- 排查进程内存：`top` 按 RES、`pmap -x <pid>`、Java 看堆 `jmap`/dump 分析是否泄漏\n- 容器里：受 cgroup limit 限制，超限被 OOM kill（exit 137），看 limit 与实际用量"},
{"domain": "linux", "section": "性能排查与调优", "ord": 9, "category": "场景设计",
 "question": "一个线上服务突然变慢，你的整体排查思路是什么？",
 "answer_md": "分层快速定位（自上而下 + 自下而上结合）：\n1. **确认现象**：是全部慢还是部分接口？什么时间开始？有没有发版/流量突增？看监控大盘（QPS、RT、错误率）\n2. **机器层**：`top`/`uptime` 看 load、CPU、`%wa`；`free` 看内存换页；`iostat` 看磁盘；`ss`/`iftop` 看网络与连接数\n3. **应用层**：线程栈（jstack/arthas thread）看是否阻塞/死锁；GC 日志看是否频繁 Full GC（STW）；连接池/线程池是否打满\n4. **依赖层**：下游 DB/缓存/RPC 是否变慢——慢 SQL（slow log）、Redis 大 key/慢命令、超时重试雪崩\n5. **方法论**：RED（Rate/Errors/Duration）看服务、USE（Utilization/Saturation/Errors）看资源；链路追踪（trace_id）定位到具体环节\n- 先止血（扩容/限流/降级/回滚）再定位根因"},
# ===================== Git =====================
{"domain": "git", "section": "基础与原理", "ord": 0, "category": "基础",
 "question": "Git 的工作区、暂存区、版本库是什么？常用命令如何在它们之间流转？",
 "answer_md": "- **工作区（Working Directory）**：你编辑的目录\n- **暂存区（Staging/Index）**：`git add` 把改动放入，准备提交的快照\n- **版本库（Repository）**：`git commit` 把暂存区永久记录为一次提交（在 .git 里）\n- 还有**远程仓库**：`git push` / `git pull`\n- 流转：\n  ```\n  工作区 --add--> 暂存区 --commit--> 本地库 --push--> 远程库\n  ```\n- 常用：`git status`（看三区状态）、`git diff`（工作区vs暂存区）、`git diff --staged`（暂存区vs版本库）、`git restore`/`git restore --staged`（撤回）"},
{"domain": "git", "section": "基础与原理", "ord": 1, "category": "进阶",
 "question": "Git 底层是怎么存储的？commit、tree、blob 是什么？快照还是差异？",
 "answer_md": "- Git 存的是**快照（snapshot）不是差异**：每次 commit 记录整个项目当时的文件树状态（未变的文件指向同一对象，不重复存）\n- 三种核心对象（按内容 SHA-1 寻址，存在 .git/objects）：\n  - **blob**：文件内容\n  - **tree**：目录结构（指向 blob 和子 tree，含文件名/权限）\n  - **commit**：指向一个顶层 tree + 父 commit + 作者/时间/message\n- **引用**：分支/tag 只是指向某个 commit 的**指针**（.git/refs），HEAD 指向当前分支\n- 这解释了为什么切分支、打 tag 都很快（只是移动 40 字节的指针），以及为什么 commit hash 能保证完整性"},
{"domain": "git", "section": "基础与原理", "ord": 2, "category": "基础",
 "question": "HEAD、分支、tag 的本质是什么？detached HEAD 是什么？",
 "answer_md": "- **分支**：一个指向 commit 的**可移动指针**，提交时自动前移（本质是 refs/heads/xxx 里存的一个 hash）\n- **HEAD**：指向「当前所在位置」的指针，通常指向某个分支（间接指向 commit）\n- **tag**：指向某个 commit 的**不可移动**标签（轻量 tag 是引用；附注 tag 是独立对象，含作者/说明/签名），用于发版\n- **detached HEAD（游离头）**：HEAD 直接指向某个 commit 而非分支（如 `git checkout <hash>`）——此时提交不属于任何分支，切走就可能丢失；要保留需 `git branch new`\n- 切换：`git switch <branch>`（新）/ `git checkout`"},
{"domain": "git", "section": "分支与协作", "ord": 3, "category": "基础",
 "question": "merge 和 rebase 的区别？各自适用什么场景？",
 "answer_md": "- **merge**：把两个分支的历史合并，产生一个**合并提交**（有两个父）——保留真实分叉历史，**非破坏性**\n- **rebase**：把当前分支的提交**逐个搬到**目标分支最新提交之后，**改写 commit hash**——历史变成一条直线、干净\n- 选择：\n  - 想要**线性、干净**的历史 → rebase（如把 feature 同步最新 main：`git rebase main`）\n  - 想**保留真实合并记录** / 合并到主干 → merge\n- **黄金法则**：**不要 rebase 已经推送/被别人使用的公共分支**（改写历史会让协作者的历史对不上）\n- 实践：本地整理用 rebase，合入主干用 merge（或 squash merge）"},
{"domain": "git", "section": "分支与协作", "ord": 4, "category": "基础",
 "question": "git pull 等于 fetch + merge 吗？--rebase 有什么区别？",
 "answer_md": "- `git fetch`：只把远程更新**下载**到本地（更新 origin/main），**不动**你的工作区和当前分支\n- `git pull` = `git fetch` + `git merge origin/<branch>`（默认）：拉取并合并\n- `git pull --rebase` = `git fetch` + `git rebase origin/<branch>`：把你的本地提交**搬到**远程最新之后\n  - 好处：避免产生大量「Merge branch」噪音提交，历史更线性\n  - 可设默认：`git config --global pull.rebase true`\n- 实践：本地有未推送提交时，`pull --rebase` 更干净；但若已有冲突复杂的合并，merge 更稳\n- 推荐先 `fetch` 看清差异（`git log HEAD..origin/main`）再决定 merge / rebase"},
{"domain": "git", "section": "分支与协作", "ord": 5, "category": "进阶",
 "question": "常见的分支管理模型有哪些？（Git Flow / GitHub Flow / 主干开发）",
 "answer_md": "- **Git Flow**：master（发布）+ develop（集成）+ feature/release/hotfix 分支。规范但**重**，适合有明确版本发布周期的项目\n- **GitHub Flow**：只有一个长期分支 main，功能开 feature 分支 → PR → review → 合并 → 部署。**简单、持续部署**友好，互联网团队常用\n- **GitLab Flow**：在 GitHub Flow 基础上加 environment 分支（pre-prod/prod），适配多环境\n- **主干开发（Trunk-Based）**：大家都往 main 提交（feature flag 控制未完成功能），分支生命周期极短。**CI/CD 成熟度高**的团队用，减少合并地狱\n- 选择看团队规模、发布频率、CI 成熟度——多数中小团队 GitHub Flow 足够"},
{"domain": "git", "section": "实战场景", "ord": 6, "category": "场景设计",
 "question": "提交错了/改错了怎么撤销？reset、revert、checkout/restore 的区别？",
 "answer_md": "- **撤销工作区修改**：`git restore <file>`（旧：`git checkout -- file`）\n- **取消暂存**：`git restore --staged <file>`（旧：`git reset HEAD file`）\n- **git reset**（移动分支指针，改写历史，用于**未推送**的提交）：\n  - `--soft`：撤销 commit，改动留在暂存区\n  - `--mixed`（默认）：撤销 commit + 取消 add，改动留工作区\n  - `--hard`：**彻底丢弃**改动（危险）\n- **git revert**：生成一个**新提交**来抵消某次提交的改动，**不改写历史** → 适合**已推送的公共分支**\n- 选择口诀：**公共分支用 revert，私有未推送用 reset**\n- 后悔药：`git reflog` 能找回 reset 丢掉的提交"},
{"domain": "git", "section": "实战场景", "ord": 7, "category": "场景设计",
 "question": "合并冲突是怎么产生的？解决流程是什么？如何减少冲突？",
 "answer_md": "- 产生：两个分支**修改了同一文件的同一区域**（或一边删一边改），Git 无法自动决定\n- 解决流程：\n  1. merge/rebase 后 `git status` 看冲突文件\n  2. 打开文件，处理 `<<<<<<< HEAD ... ======= ... >>>>>>>` 标记，保留正确内容、删掉标记\n  3. `git add <file>` 标记已解决\n  4. merge：`git commit`；rebase：`git rebase --continue`（中途想放弃 `--abort`）\n- 工具：`git mergetool`、IDE 三方合并视图\n- **减少冲突**：\n  - 小步提交、**频繁同步主干**（别让分支存活太久）\n  - 团队约定代码格式（避免格式化造成的伪冲突）、模块化减少同文件改动\n  - 明确文件/模块归属，沟通在先"},
{"domain": "git", "section": "实战场景", "ord": 8, "category": "场景设计",
 "question": "怎么整理提交历史？rebase -i、squash、cherry-pick 怎么用？",
 "answer_md": "- **交互式 rebase** `git rebase -i HEAD~5`：整理最近 5 个提交，可对每个选择：\n  - `pick` 保留、`reword` 改 message、`squash`/`fixup` **合并到上一个**、`drop` 删除、`edit` 暂停修改、调整行序可**重排**\n- 典型场景：把开发中零碎的「fix typo」「wip」提交 **squash 成一个干净提交**再发 PR\n- **cherry-pick** `git cherry-pick <hash>`：把**某个/某些提交**单独摘到当前分支（如把 hotfix 同步到多个版本分支）\n- **amend** `git commit --amend`：修补**最近一次**提交（改 message 或补文件）\n- ⚠️ 都会改写 hash → 只在**未推送或私有分支**上做；已共享的别动（否则要 force push 影响他人）"},
{"domain": "git", "section": "实战场景", "ord": 9, "category": "场景设计",
 "question": "不小心提交了密码/大文件，怎么从历史里彻底删除？",
 "answer_md": "- **只是最近一次、还没 push**：`git rm --cached secret`，加进 `.gitignore`，`git commit --amend`\n- **已经进入历史（多个提交）**：仅删当前文件不够，旧 commit 里仍有 → 要**重写历史**：\n  - 推荐 `git filter-repo --path secret --invert-paths`（官方推荐，快）\n  - 或 BFG：`bfg --delete-files secret`、`bfg --replace-text passwords.txt`\n  - 老办法 `git filter-branch`（慢、已不推荐）\n- 重写后 `git push --force`（需协调团队重新 clone）\n- ⚠️ **最关键**：凡是 push 到远程/被人看到的**密钥视为已泄露**，必须**立即吊销/轮换**（改密码、重置 token），删历史只是补救\n- 预防：`.gitignore` 屏蔽配置/密钥、用环境变量、pre-commit 钩子扫描（gitleaks）"},
]

data = json.loads(SEED.read_text(encoding="utf-8"))
existing = {(q["domain"], q["question"]) for q in data}
added = 0
for q in NEW:
    if (q["domain"], q["question"]) in existing:
        continue
    data.append(q)
    added += 1
SEED.write_text(json.dumps(data, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
print(f"新增 {added} 题，题库共 {len(data)} 题")
