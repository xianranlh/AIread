# LeetCode Hot 100 讲义 · Part 5：图论(4) + 回溯(8) + 二分查找(6)
PROBLEMS = [
{"cat": "graph", "lc": 200, "t": "岛屿数量", "d": "中等", "slug": "number-of-islands", "md": r'''
**题目**：网格中 '1' 是陆地、'0' 是水，上下左右相连的陆地组成岛屿，数一数有几座岛。

#### 💡 思路（白话）

- 遍历网格，每遇到一个 '1' 就答案 +1，然后从它出发 **DFS 把整座岛「淹掉」**（把相连的 '1' 全改成 '0'）——这样同一座岛不会被重复计数。
- DFS 写法：越界或遇水就返回；否则淹掉当前格，向四个方向递归。
- 这个套路叫「洪水填充（Flood Fill）」，是所有网格 DFS 题的模板。

#### ☕ Java

```java
class Solution {
    public int numIslands(char[][] grid) {
        int count = 0;
        for (int i = 0; i < grid.length; i++)
            for (int j = 0; j < grid[0].length; j++)
                if (grid[i][j] == '1') {
                    count++;
                    sink(grid, i, j);     // 淹掉整座岛
                }
        return count;
    }
    private void sink(char[][] g, int i, int j) {
        if (i < 0 || i >= g.length || j < 0 || j >= g[0].length || g[i][j] != '1')
            return;
        g[i][j] = '0';                    // 淹掉，兼做「已访问」标记
        sink(g, i + 1, j); sink(g, i - 1, j);
        sink(g, i, j + 1); sink(g, i, j - 1);
    }
}
```

#### 🐍 Python

```python
class Solution:
    def numIslands(self, grid: List[List[str]]) -> int:
        m, n = len(grid), len(grid[0])
        def sink(i, j):
            if not (0 <= i < m and 0 <= j < n) or grid[i][j] != '1':
                return
            grid[i][j] = '0'
            sink(i + 1, j); sink(i - 1, j); sink(i, j + 1); sink(i, j - 1)
        count = 0
        for i in range(m):
            for j in range(n):
                if grid[i][j] == '1':
                    count += 1
                    sink(i, j)
        return count
```

#### ⏱ 复杂度

时间 O(mn)，空间 O(mn)（递归栈最坏情况）。

**小白提示**：把「检查越界 + 检查值」放在递归函数**开头**统一处理（先递归再判断），代码比「调用前判断」干净得多。网格 DFS 一通百通：岛屿周长、最大岛屿面积都是它换皮。
'''},

{"cat": "graph", "lc": 994, "t": "腐烂的橘子", "d": "中等", "slug": "rotting-oranges", "md": r'''
**题目**：网格里 2 是烂橘子、1 是好橘子、0 是空。每分钟烂橘子使上下左右的好橘子腐烂。求全部烂掉需要几分钟；不可能则返回 -1。

#### 💡 思路（白话）

- 「同时从多个起点向外扩散，求扩散时间」= **多源 BFS**：把**所有**烂橘子先全部入队（同一起跑线），一层 BFS 等于一分钟。
- 流程：统计好橘子数 fresh，烂橘子全入队 → 逐层 BFS，每腐烂一个 `fresh--` → 结束后 fresh > 0 说明有橘子永远烂不到，返回 -1。
- 和层序遍历（102）一模一样的「先记 size 再弹」分层技巧。

#### ☕ Java

```java
class Solution {
    public int orangesRotting(int[][] grid) {
        int m = grid.length, n = grid[0].length, fresh = 0;
        Queue<int[]> queue = new LinkedList<>();
        for (int i = 0; i < m; i++)
            for (int j = 0; j < n; j++) {
                if (grid[i][j] == 2) queue.offer(new int[]{i, j});
                else if (grid[i][j] == 1) fresh++;
            }
        int minutes = 0;
        int[][] dirs = {{1,0},{-1,0},{0,1},{0,-1}};
        while (!queue.isEmpty() && fresh > 0) {
            minutes++;                                  // 新的一分钟
            for (int size = queue.size(); size > 0; size--) {
                int[] cur = queue.poll();
                for (int[] d : dirs) {
                    int x = cur[0] + d[0], y = cur[1] + d[1];
                    if (x >= 0 && x < m && y >= 0 && y < n && grid[x][y] == 1) {
                        grid[x][y] = 2;                 // 腐烂
                        fresh--;
                        queue.offer(new int[]{x, y});
                    }
                }
            }
        }
        return fresh == 0 ? minutes : -1;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def orangesRotting(self, grid: List[List[int]]) -> int:
        m, n = len(grid), len(grid[0])
        queue, fresh = deque(), 0
        for i in range(m):
            for j in range(n):
                if grid[i][j] == 2: queue.append((i, j))
                elif grid[i][j] == 1: fresh += 1
        minutes = 0
        while queue and fresh:
            minutes += 1
            for _ in range(len(queue)):
                i, j = queue.popleft()
                for x, y in ((i+1,j),(i-1,j),(i,j+1),(i,j-1)):
                    if 0 <= x < m and 0 <= y < n and grid[x][y] == 1:
                        grid[x][y] = 2
                        fresh -= 1
                        queue.append((x, y))
        return minutes if fresh == 0 else -1
```

#### ⏱ 复杂度

时间 O(mn)，空间 O(mn)。

**小白提示**：循环条件带上 `fresh > 0`，否则「最后一层烂橘子没有可感染的」也会多算一分钟。「求最短时间/最少步数」一律 BFS，「数连通块」一律 DFS——记住这个分工。
'''},

{"cat": "graph", "lc": 207, "t": "课程表", "d": "中等", "slug": "course-schedule", "md": r'''
**题目**：n 门课，`[a, b]` 表示修 a 前必须先修 b。判断能否修完所有课（即：依赖关系里**有没有环**）。

#### 💡 思路（白话）

- 把课程看成节点、先修关系看成有向边，**能修完 ⇔ 图无环**。判环用**拓扑排序（BFS 版）**：
  1. 统计每门课的**入度**（有几门前置课）；
  2. 入度为 0 的课（没有前置）入队，可以直接修；
  3. 每修一门课，它指向的课入度减 1；减到 0 就也入队；
  4. 最后修完的课数 == n → 无环。
- 直观理解：不断「摘掉没有依赖的节点」，摘不完说明剩下的互相卡死（环）。

#### ☕ Java

```java
class Solution {
    public boolean canFinish(int numCourses, int[][] prerequisites) {
        List<List<Integer>> graph = new ArrayList<>();   // 邻接表
        for (int i = 0; i < numCourses; i++) graph.add(new ArrayList<>());
        int[] indeg = new int[numCourses];
        for (int[] p : prerequisites) {
            graph.get(p[1]).add(p[0]);    // b -> a
            indeg[p[0]]++;
        }
        Queue<Integer> queue = new LinkedList<>();
        for (int i = 0; i < numCourses; i++)
            if (indeg[i] == 0) queue.offer(i);
        int finished = 0;
        while (!queue.isEmpty()) {
            int course = queue.poll();
            finished++;
            for (int next : graph.get(course))
                if (--indeg[next] == 0) queue.offer(next);
        }
        return finished == numCourses;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def canFinish(self, numCourses: int, prerequisites: List[List[int]]) -> bool:
        graph = defaultdict(list)
        indeg = [0] * numCourses
        for a, b in prerequisites:
            graph[b].append(a)
            indeg[a] += 1
        queue = deque(i for i in range(numCourses) if indeg[i] == 0)
        finished = 0
        while queue:
            course = queue.popleft()
            finished += 1
            for nxt in graph[course]:
                indeg[nxt] -= 1
                if indeg[nxt] == 0:
                    queue.append(nxt)
        return finished == numCourses
```

#### ⏱ 复杂度

时间 O(V + E)，空间 O(V + E)。

**小白提示**：拓扑排序是工程中真正常用的算法（Maven 依赖解析、任务调度、Excel 公式计算都靠它），面试常考「讲讲思路」。进阶版「课程表 II」只多一步：把弹出顺序记下来就是修课顺序。
'''},

{"cat": "graph", "lc": 208, "t": "实现 Trie (前缀树)", "d": "中等", "slug": "implement-trie-prefix-tree", "md": r'''
**题目**：实现 Trie：`insert(word)` 插入、`search(word)` 查完整单词、`startsWith(prefix)` 查前缀。

#### 💡 思路（白话）

- Trie 是一棵「字母树」：每个节点有 26 个孩子格子，从根往下走的一条路径拼出一个前缀。单词结尾的节点打上 `isEnd` 标记。
- 三个操作都是同一个动作——**沿着字母一路往下走**：
  - insert：没路就修路（建节点），走完打标记；
  - search：没路就 false，走完看 `isEnd`；
  - startsWith：没路就 false，走完即 true（不用看标记）。

#### ☕ Java

```java
class Trie {
    private Trie[] children = new Trie[26];
    private boolean isEnd = false;

    public Trie() {}

    public void insert(String word) {
        Trie node = this;
        for (char c : word.toCharArray()) {
            int i = c - 'a';
            if (node.children[i] == null) node.children[i] = new Trie();
            node = node.children[i];
        }
        node.isEnd = true;
    }
    public boolean search(String word) {
        Trie node = find(word);
        return node != null && node.isEnd;
    }
    public boolean startsWith(String prefix) {
        return find(prefix) != null;
    }
    private Trie find(String s) {       // 沿字母往下走
        Trie node = this;
        for (char c : s.toCharArray()) {
            node = node.children[c - 'a'];
            if (node == null) return null;
        }
        return node;
    }
}
```

#### 🐍 Python

```python
class Trie:
    def __init__(self):
        self.children = {}
        self.is_end = False

    def insert(self, word: str) -> None:
        node = self
        for c in word:
            node = node.children.setdefault(c, Trie())
        node.is_end = True

    def _find(self, s):
        node = self
        for c in s:
            node = node.children.get(c)
            if node is None:
                return None
        return node

    def search(self, word: str) -> bool:
        node = self._find(word)
        return node is not None and node.is_end

    def startsWith(self, prefix: str) -> bool:
        return self._find(prefix) is not None
```

#### ⏱ 复杂度

每个操作 O(单词长度)，空间 O(总字符数 × 26)。

**小白提示**：search 和 startsWith 唯一的区别就是要不要看 `isEnd`，抽一个 `find` 复用。Trie 在工程里就是搜索框自动补全、敏感词过滤的底层结构，面试讲应用场景是加分项。
'''},

{"cat": "backtracking", "lc": 46, "t": "全排列", "d": "中等", "slug": "permutations", "md": r'''
**题目**：返回不含重复数字的数组的**所有排列**。`[1,2,3]` → 6 种排列。

#### 💡 思路（白话）

- 回溯模板的标准示范。想象在填 n 个空位：每个空位依次试每个**还没用过**的数。
- `path` 记当前已填的数，`used[i]` 标记 nums[i] 用没用过。
- `path` 填满 → 记录一份**拷贝**（重要！）；否则遍历所有数：没用过就「选它 → 递归 → 撤销」。

#### ☕ Java

```java
class Solution {
    public List<List<Integer>> permute(int[] nums) {
        List<List<Integer>> res = new ArrayList<>();
        backtrack(nums, new ArrayList<>(), new boolean[nums.length], res);
        return res;
    }
    private void backtrack(int[] nums, List<Integer> path, boolean[] used,
                           List<List<Integer>> res) {
        if (path.size() == nums.length) {
            res.add(new ArrayList<>(path));   // 必须拷贝！
            return;
        }
        for (int i = 0; i < nums.length; i++) {
            if (used[i]) continue;
            path.add(nums[i]); used[i] = true;    // 做选择
            backtrack(nums, path, used, res);
            path.remove(path.size() - 1); used[i] = false;  // 撤销
        }
    }
}
```

#### 🐍 Python

```python
class Solution:
    def permute(self, nums: List[int]) -> List[List[int]]:
        res, path = [], []
        used = [False] * len(nums)
        def backtrack():
            if len(path) == len(nums):
                res.append(path[:])        # 拷贝
                return
            for i, x in enumerate(nums):
                if used[i]:
                    continue
                path.append(x); used[i] = True
                backtrack()
                path.pop(); used[i] = False
        backtrack()
        return res
```

#### ⏱ 复杂度

时间 O(n × n!)，空间 O(n)。

**小白提示**：两个新手必踩的坑：① `res.add(path)` 不拷贝——最后所有结果都是同一个空列表；② 忘了撤销——后面的分支被污染。把「选择 → 递归 → 撤销」念成口诀。
'''},

{"cat": "backtracking", "lc": 78, "t": "子集", "d": "中等", "slug": "subsets", "md": r'''
**题目**：返回数组的所有子集（幂集）。`[1,2,3]` → 8 个子集（含空集）。

#### 💡 思路（白话）

- 和排列的区别：子集**无顺序**，`[1,2]` 和 `[2,1]` 是同一个。避免重复的办法：**只往后选**——用 `start` 参数，第 i 层只能从下标 start 开始选。
- 另一个不同：**每个中间状态都是答案**（不用等到「满」），进入递归就先记录当前 path。

#### ☕ Java

```java
class Solution {
    public List<List<Integer>> subsets(int[] nums) {
        List<List<Integer>> res = new ArrayList<>();
        backtrack(nums, 0, new ArrayList<>(), res);
        return res;
    }
    private void backtrack(int[] nums, int start, List<Integer> path,
                           List<List<Integer>> res) {
        res.add(new ArrayList<>(path));       // 每个节点都是一个子集
        for (int i = start; i < nums.length; i++) {
            path.add(nums[i]);                // 选
            backtrack(nums, i + 1, path, res);// 只能往后选
            path.remove(path.size() - 1);     // 撤销
        }
    }
}
```

#### 🐍 Python

```python
class Solution:
    def subsets(self, nums: List[int]) -> List[List[int]]:
        res, path = [], []
        def backtrack(start):
            res.append(path[:])
            for i in range(start, len(nums)):
                path.append(nums[i])
                backtrack(i + 1)
                path.pop()
        backtrack(0)
        return res
```

#### ⏱ 复杂度

时间 O(n × 2ⁿ)，空间 O(n)。

**小白提示**：记住分水岭：**排列用 used 数组（每层都从头选），组合/子集用 start 参数（只往后选）**。分清这两类，回溯题就解决了一大半。
'''},

{"cat": "backtracking", "lc": 17, "t": "电话号码的字母组合", "d": "中等", "slug": "letter-combinations-of-a-phone-number", "md": r'''
**题目**：九键手机上，数字 2-9 各对应几个字母。给数字串，返回所有可能的字母组合。`"23"` → `["ad","ae","af","bd","be","bf","cd","ce","cf"]`。

#### 💡 思路（白话）

- 多层 for 循环的层数不固定（取决于输入长度）→ 用递归代替：第 i 层处理第 i 个数字，枚举它的每个字母。
- `index` 指当前处理到第几个数字，走到尽头就收集结果。
- 因为每层枚举的是「不同数字的字母」，互不冲突，不需要 used 也不需要去重。

#### ☕ Java

```java
class Solution {
    private static final String[] LETTERS =
        {"", "", "abc", "def", "ghi", "jkl", "mno", "pqrs", "tuv", "wxyz"};

    public List<String> letterCombinations(String digits) {
        List<String> res = new ArrayList<>();
        if (digits.isEmpty()) return res;
        backtrack(digits, 0, new StringBuilder(), res);
        return res;
    }
    private void backtrack(String digits, int index, StringBuilder path, List<String> res) {
        if (index == digits.length()) {
            res.add(path.toString());
            return;
        }
        for (char c : LETTERS[digits.charAt(index) - '0'].toCharArray()) {
            path.append(c);                       // 选
            backtrack(digits, index + 1, path, res);
            path.deleteCharAt(path.length() - 1); // 撤销
        }
    }
}
```

#### 🐍 Python

```python
class Solution:
    def letterCombinations(self, digits: str) -> List[str]:
        if not digits:
            return []
        letters = {'2':'abc','3':'def','4':'ghi','5':'jkl',
                   '6':'mno','7':'pqrs','8':'tuv','9':'wxyz'}
        res, path = [], []
        def backtrack(index):
            if index == len(digits):
                res.append(''.join(path))
                return
            for c in letters[digits[index]]:
                path.append(c)
                backtrack(index + 1)
                path.pop()
        backtrack(0)
        return res
```

#### ⏱ 复杂度

时间 O(4ⁿ × n)，空间 O(n)。

**小白提示**：把回溯过程画成一棵树：第一层分 a/b/c 三叉，每叉再分 d/e/f……「回溯 = 决策树的深度优先遍历」，这棵树画一次胜读十遍代码。
'''},

{"cat": "backtracking", "lc": 39, "t": "组合总和", "d": "中等", "slug": "combination-sum", "md": r'''
**题目**：从无重复元素的数组中选数（**每个数可以无限次重复选**），找出所有和为 target 的组合。

#### 💡 思路（白话）

- 子集模板的变体，两处改动：
  1. 终止条件变成「剩余 target == 0 收集；< 0 剪枝返回」；
  2. **允许重复选自己**：递归时传 `i` 而不是 `i + 1`（下一层还能从我开始选）。
- 仍然用 start 保证组合不重复（`[2,3]` 和 `[3,2]` 只出现一次）。

#### ☕ Java

```java
class Solution {
    public List<List<Integer>> combinationSum(int[] candidates, int target) {
        List<List<Integer>> res = new ArrayList<>();
        backtrack(candidates, 0, target, new ArrayList<>(), res);
        return res;
    }
    private void backtrack(int[] nums, int start, int remain,
                           List<Integer> path, List<List<Integer>> res) {
        if (remain == 0) { res.add(new ArrayList<>(path)); return; }
        if (remain < 0) return;                  // 超了，剪枝
        for (int i = start; i < nums.length; i++) {
            path.add(nums[i]);
            backtrack(nums, i, remain - nums[i], path, res); // 传 i：可重复选自己
            path.remove(path.size() - 1);
        }
    }
}
```

#### 🐍 Python

```python
class Solution:
    def combinationSum(self, candidates: List[int], target: int) -> List[List[int]]:
        res, path = [], []
        def backtrack(start, remain):
            if remain == 0:
                res.append(path[:])
                return
            if remain < 0:
                return
            for i in range(start, len(candidates)):
                path.append(candidates[i])
                backtrack(i, remain - candidates[i])   # i 而不是 i+1
                path.pop()
        backtrack(0, target)
        return res
```

#### ⏱ 复杂度

时间指数级（取决于解的数量），空间 O(target/min)。

**小白提示**：`i` 还是 `i + 1`，一字之差决定「能否重复选自己」——这是组合类回溯题最常考的变化点。先排序再配合 `remain < nums[i]` 时 break，可以剪枝提速。
'''},

{"cat": "backtracking", "lc": 22, "t": "括号生成", "d": "中等", "slug": "generate-parentheses", "md": r'''
**题目**：生成所有由 n 对括号组成的**有效**括号组合。n=3 → `["((()))","(()())","(())()","()(())","()()()"]`。

#### 💡 思路（白话）

- 每一步只有两个选择：放 `(` 或放 `)`。但要保证有效，加两条规则：
  1. `(` 的数量 < n 才能放 `(`；
  2. `)` 的数量 < `(` 的数量才能放 `)`（先有开才有关）。
- 满足规则往下走，长度到 2n 就是一个合法答案。**边生成边约束**，根本不会产生无效组合，比「全生成再过滤」高效得多。

#### ☕ Java

```java
class Solution {
    public List<String> generateParenthesis(int n) {
        List<String> res = new ArrayList<>();
        backtrack(n, 0, 0, new StringBuilder(), res);
        return res;
    }
    private void backtrack(int n, int open, int close, StringBuilder path, List<String> res) {
        if (path.length() == 2 * n) {
            res.add(path.toString());
            return;
        }
        if (open < n) {                         // 还能放 (
            path.append('(');
            backtrack(n, open + 1, close, path, res);
            path.deleteCharAt(path.length() - 1);
        }
        if (close < open) {                     // 还能放 )
            path.append(')');
            backtrack(n, open, close + 1, path, res);
            path.deleteCharAt(path.length() - 1);
        }
    }
}
```

#### 🐍 Python

```python
class Solution:
    def generateParenthesis(self, n: int) -> List[str]:
        res, path = [], []
        def backtrack(open_n, close_n):
            if len(path) == 2 * n:
                res.append(''.join(path))
                return
            if open_n < n:
                path.append('(')
                backtrack(open_n + 1, close_n)
                path.pop()
            if close_n < open_n:
                path.append(')')
                backtrack(open_n, close_n + 1)
                path.pop()
        backtrack(0, 0)
        return res
```

#### ⏱ 复杂度

时间 O(4ⁿ/√n)（卡特兰数），空间 O(n)。

**小白提示**：本题展示了回溯的精髓——**用约束条件剪掉不合法的分支**，而不是生成后再检查。「close < open 才能放右括号」一句话保证了所有结果合法。
'''},

{"cat": "backtracking", "lc": 79, "t": "单词搜索", "d": "中等", "slug": "word-search", "md": r'''
**题目**：在字母网格中判断能否沿上下左右（同一格不能重复用）走出给定单词。

#### 💡 思路（白话）

- 网格 DFS（岛屿数量）+ 回溯（用过要还原）的结合：
  - 以每个格子为起点尝试；
  - `dfs(i, j, k)`：当前在 (i,j)，匹配到单词第 k 个字符。格子字符不等于 `word[k]` → false；k 是最后一个字符 → true；
  - 否则**把当前格子临时标记为已用**（改成特殊字符），四个方向递归，回来后**还原**——这一步就是回溯。

#### ☕ Java

```java
class Solution {
    public boolean exist(char[][] board, String word) {
        for (int i = 0; i < board.length; i++)
            for (int j = 0; j < board[0].length; j++)
                if (dfs(board, word, i, j, 0)) return true;
        return false;
    }
    private boolean dfs(char[][] b, String word, int i, int j, int k) {
        if (i < 0 || i >= b.length || j < 0 || j >= b[0].length
            || b[i][j] != word.charAt(k)) return false;
        if (k == word.length() - 1) return true;
        b[i][j] = '#';                          // 占用
        boolean found = dfs(b, word, i + 1, j, k + 1)
                     || dfs(b, word, i - 1, j, k + 1)
                     || dfs(b, word, i, j + 1, k + 1)
                     || dfs(b, word, i, j - 1, k + 1);
        b[i][j] = word.charAt(k);               // 还原（回溯）
        return found;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def exist(self, board: List[List[str]], word: str) -> bool:
        m, n = len(board), len(board[0])
        def dfs(i, j, k):
            if not (0 <= i < m and 0 <= j < n) or board[i][j] != word[k]:
                return False
            if k == len(word) - 1:
                return True
            board[i][j] = '#'
            found = (dfs(i+1, j, k+1) or dfs(i-1, j, k+1) or
                     dfs(i, j+1, k+1) or dfs(i, j-1, k+1))
            board[i][j] = word[k]
            return found
        return any(dfs(i, j, 0) for i in range(m) for j in range(n))
```

#### ⏱ 复杂度

时间 O(mn × 3^L)（L 为单词长），空间 O(L)。

**小白提示**：用「改格子再还原」代替单独的 visited 数组，省空间又不容易忘记还原。`||` 的短路特性让找到一条路就立刻层层返回 true。
'''},

{"cat": "backtracking", "lc": 131, "t": "分割回文串", "d": "中等", "slug": "palindrome-partitioning", "md": r'''
**题目**：把字符串分割成若干子串，要求每个子串都是回文，返回所有分割方案。`"aab"` → `[["a","a","b"],["aa","b"]]`。

#### 💡 思路（白话）

- 回溯的「选择」是**切哪一刀**：站在位置 start，尝试把 `s[start..i]` 作为下一段——前提是它是回文。
- 是回文 → 选它，递归处理 `i+1` 之后的部分，回来撤销；
- `start` 走到字符串尽头，说明每一段都是回文，收集方案。

#### ☕ Java

```java
class Solution {
    public List<List<String>> partition(String s) {
        List<List<String>> res = new ArrayList<>();
        backtrack(s, 0, new ArrayList<>(), res);
        return res;
    }
    private void backtrack(String s, int start, List<String> path, List<List<String>> res) {
        if (start == s.length()) {
            res.add(new ArrayList<>(path));
            return;
        }
        for (int i = start; i < s.length(); i++) {
            if (!isPalin(s, start, i)) continue;    // 这一刀切出来不回文，跳过
            path.add(s.substring(start, i + 1));
            backtrack(s, i + 1, path, res);
            path.remove(path.size() - 1);
        }
    }
    private boolean isPalin(String s, int l, int r) {
        while (l < r)
            if (s.charAt(l++) != s.charAt(r--)) return false;
        return true;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def partition(self, s: str) -> List[List[str]]:
        res, path = [], []
        def backtrack(start):
            if start == len(s):
                res.append(path[:])
                return
            for i in range(start, len(s)):
                sub = s[start:i + 1]
                if sub == sub[::-1]:       # 是回文才往下走
                    path.append(sub)
                    backtrack(i + 1)
                    path.pop()
        backtrack(0)
        return res
```

#### ⏱ 复杂度

时间 O(n × 2ⁿ)，空间 O(n)。

**小白提示**：「分割问题」的回溯套路：start 是这一段的起点，i 是这一刀的终点，递归从 `i+1` 继续。和子集题对照看，结构几乎一样，只是「选元素」变成了「选切割点」。
'''},

{"cat": "backtracking", "lc": 51, "t": "N 皇后", "d": "困难", "slug": "n-queens", "md": r'''
**题目**：在 n×n 棋盘放 n 个皇后，任意两个不能同行、同列、同斜线。返回所有摆法。

#### 💡 思路（白话）

- **逐行放置**（一行一个，天然不同行），每行尝试每一列——「选择」是列号。
- 怎么快速判断不冲突？三个 set：
  - `cols`：被占用的列；
  - `diag1`：左上→右下对角线，特征值 `行 - 列` 相同；
  - `diag2`：右上→左下对角线，特征值 `行 + 列` 相同。
- 放下 → 三个 set 登记 → 递归下一行 → 撤销。放满 n 行收集棋盘。

#### ☕ Java

```java
class Solution {
    public List<List<String>> solveNQueens(int n) {
        List<List<String>> res = new ArrayList<>();
        int[] queens = new int[n];               // queens[row] = 该行皇后的列
        backtrack(n, 0, queens, new HashSet<>(), new HashSet<>(), new HashSet<>(), res);
        return res;
    }
    private void backtrack(int n, int row, int[] queens, Set<Integer> cols,
                           Set<Integer> d1, Set<Integer> d2, List<List<String>> res) {
        if (row == n) { res.add(draw(queens, n)); return; }
        for (int col = 0; col < n; col++) {
            if (cols.contains(col) || d1.contains(row - col) || d2.contains(row + col))
                continue;                        // 冲突，剪枝
            queens[row] = col;
            cols.add(col); d1.add(row - col); d2.add(row + col);
            backtrack(n, row + 1, queens, cols, d1, d2, res);
            cols.remove(col); d1.remove(row - col); d2.remove(row + col);
        }
    }
    private List<String> draw(int[] queens, int n) {
        List<String> board = new ArrayList<>();
        for (int q : queens) {
            char[] row = new char[n];
            Arrays.fill(row, '.');
            row[q] = 'Q';
            board.add(new String(row));
        }
        return board;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def solveNQueens(self, n: int) -> List[List[str]]:
        res, queens = [], []
        cols, d1, d2 = set(), set(), set()
        def backtrack(row):
            if row == n:
                res.append(['.' * c + 'Q' + '.' * (n - c - 1) for c in queens])
                return
            for col in range(n):
                if col in cols or (row - col) in d1 or (row + col) in d2:
                    continue
                queens.append(col)
                cols.add(col); d1.add(row - col); d2.add(row + col)
                backtrack(row + 1)
                queens.pop()
                cols.remove(col); d1.remove(row - col); d2.remove(row + col)
        backtrack(0)
        return res
```

#### ⏱ 复杂度

时间 O(n!)，空间 O(n)。

**小白提示**：记住两条对角线的特征值：「**r - c 同为一条 ↘ 线，r + c 同为一条 ↙ 线**」。N 皇后是回溯的毕业考，把它写出来，回溯专题就算通关了。
'''},

{"cat": "binary-search", "lc": 35, "t": "搜索插入位置", "d": "简单", "slug": "search-insert-position", "md": r'''
**题目**：有序数组中找 target，找到返回下标；找不到返回它应该插入的位置。要求 O(log n)。

#### 💡 思路（白话）

- 标准二分模板（左闭右闭）。本题真正要找的是「**第一个 ≥ target 的位置**」：
  - `nums[mid] < target` → 答案在右半边，`left = mid + 1`；
  - 否则 → mid 可能是答案，但先去左边找更小的，`right = mid - 1`。
- 循环结束时 `left` 正好停在第一个 ≥ target 的位置——找到了它是 target 的下标，没找到它就是插入位置，一个返回值通吃。

#### ☕ Java

```java
class Solution {
    public int searchInsert(int[] nums, int target) {
        int left = 0, right = nums.length - 1;
        while (left <= right) {
            int mid = left + (right - left) / 2;   // 防溢出写法
            if (nums[mid] < target) left = mid + 1;
            else right = mid - 1;
        }
        return left;     // 第一个 >= target 的位置
    }
}
```

#### 🐍 Python

```python
class Solution:
    def searchInsert(self, nums: List[int], target: int) -> int:
        left, right = 0, len(nums) - 1
        while left <= right:
            mid = (left + right) // 2
            if nums[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        return left
```

#### ⏱ 复杂度

时间 O(log n)，空间 O(1)。

**小白提示**：把「**循环结束后 left = 第一个 ≥ target 的位置**」当定理背下来，下一题「查找首尾位置」直接复用。Java 写 `left + (right-left)/2` 防止 `left+right` 溢出，面试细节分。
'''},

{"cat": "binary-search", "lc": 74, "t": "搜索二维矩阵", "d": "中等", "slug": "search-a-2d-matrix", "md": r'''
**题目**：矩阵每行升序，且**每行第一个数大于上一行最后一个数**（整体展开就是有序的）。判断 target 是否存在。

#### 💡 思路（白话）

- 既然「按行展开是一个有序数组」，就把它当一维数组二分，只是访问时把一维下标翻译回二维：
  - `下标 k` → `行 = k / 列数`，`列 = k % 列数`。
- 注意和「搜索二维矩阵 II」（240）区分：那题只保证行列各自有序，用右上角楼梯走法；这题更强的有序性允许直接整体二分，O(log(mn))。

#### ☕ Java

```java
class Solution {
    public boolean searchMatrix(int[][] matrix, int target) {
        int m = matrix.length, n = matrix[0].length;
        int left = 0, right = m * n - 1;
        while (left <= right) {
            int mid = left + (right - left) / 2;
            int val = matrix[mid / n][mid % n];   // 一维下标 → 二维
            if (val == target) return true;
            else if (val < target) left = mid + 1;
            else right = mid - 1;
        }
        return false;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def searchMatrix(self, matrix: List[List[int]], target: int) -> bool:
        m, n = len(matrix), len(matrix[0])
        left, right = 0, m * n - 1
        while left <= right:
            mid = (left + right) // 2
            val = matrix[mid // n][mid % n]
            if val == target:
                return True
            elif val < target:
                left = mid + 1
            else:
                right = mid - 1
        return False
```

#### ⏱ 复杂度

时间 O(log(mn))，空间 O(1)。

**小白提示**：`mid / n` 是行、`mid % n` 是列（n 是**列数**）——除和模别写反。这个「二维拍平成一维」的技巧在堆（用数组存完全二叉树）里也会见到。
'''},

{"cat": "binary-search", "lc": 34, "t": "在排序数组中查找元素的第一个和最后一个位置", "d": "中等", "slug": "find-first-and-last-position-of-element-in-sorted-array", "md": r'''
**题目**：有序数组中找 target 出现的起始和结束下标，不存在返回 `[-1,-1]`。要求 O(log n)。

#### 💡 思路（白话）

- 拆成两次「找边界」的二分：
  - 起始位置 = **第一个 ≥ target** 的位置（35 题的定理直接用）；
  - 结束位置 = **第一个 ≥ target+1** 的位置 **再减 1**（妙！「最后一个 = 下一个值的第一个的前面」）。
- 写一个 `lowerBound(target)` 函数调用两次，几乎不用写新代码。
- 最后检查：起始位置越界或值不等于 target → 不存在。

#### ☕ Java

```java
class Solution {
    public int[] searchRange(int[] nums, int target) {
        int start = lowerBound(nums, target);
        if (start == nums.length || nums[start] != target)
            return new int[]{-1, -1};
        int end = lowerBound(nums, target + 1) - 1;
        return new int[]{start, end};
    }
    private int lowerBound(int[] nums, int target) {  // 第一个 >= target 的位置
        int left = 0, right = nums.length - 1;
        while (left <= right) {
            int mid = left + (right - left) / 2;
            if (nums[mid] < target) left = mid + 1;
            else right = mid - 1;
        }
        return left;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def searchRange(self, nums: List[int], target: int) -> List[int]:
        start = bisect_left(nums, target)        # 标准库就是 lowerBound
        if start == len(nums) or nums[start] != target:
            return [-1, -1]
        end = bisect_left(nums, target + 1) - 1
        return [start, end]
```

#### ⏱ 复杂度

时间 O(log n)，空间 O(1)。

**小白提示**：「找 target+1 的左边界再减一」这个转化让你只需要维护**一个**二分函数，不用写容易出错的「右边界二分」。Python 的 `bisect_left` 就是 lowerBound，刷题可以直接用。
'''},

{"cat": "binary-search", "lc": 33, "t": "搜索旋转排序数组", "d": "中等", "slug": "search-in-rotated-sorted-array", "md": r'''
**题目**：升序数组在某个位置被旋转过（如 `[4,5,6,7,0,1,2]`），找 target 的下标，要求 O(log n)。

#### 💡 思路（白话）

- 旋转后虽然整体无序，但从 mid 切开，**必有一半是完全有序的**。
- 每轮三步：
  1. `nums[mid] == target` → 返回；
  2. 判断哪半有序：`nums[left] <= nums[mid]` → 左半有序，否则右半有序；
  3. 看 target 在不在**有序的那半**的范围内：在 → 去那半找；不在 → 去另一半。
- 「在有序半边内」可以用两端值精确判断，这就是决策依据。

#### ☕ Java

```java
class Solution {
    public int search(int[] nums, int target) {
        int left = 0, right = nums.length - 1;
        while (left <= right) {
            int mid = left + (right - left) / 2;
            if (nums[mid] == target) return mid;
            if (nums[left] <= nums[mid]) {            // 左半有序
                if (nums[left] <= target && target < nums[mid])
                    right = mid - 1;                  // target 在左半
                else left = mid + 1;
            } else {                                  // 右半有序
                if (nums[mid] < target && target <= nums[right])
                    left = mid + 1;                   // target 在右半
                else right = mid - 1;
            }
        }
        return -1;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def search(self, nums: List[int], target: int) -> int:
        left, right = 0, len(nums) - 1
        while left <= right:
            mid = (left + right) // 2
            if nums[mid] == target:
                return mid
            if nums[left] <= nums[mid]:               # 左半有序
                if nums[left] <= target < nums[mid]:
                    right = mid - 1
                else:
                    left = mid + 1
            else:                                     # 右半有序
                if nums[mid] < target <= nums[right]:
                    left = mid + 1
                else:
                    right = mid - 1
        return -1
```

#### ⏱ 复杂度

时间 O(log n)，空间 O(1)。

**小白提示**：判断左半有序用 `<=`（mid 可能等于 left，单元素也算有序）。本题的思维升级：二分不一定要求全局有序，**只要每次能确定「答案在哪一半」就能二分**。
'''},

{"cat": "binary-search", "lc": 153, "t": "寻找旋转排序数组中的最小值", "d": "中等", "slug": "find-minimum-in-rotated-sorted-array", "md": r'''
**题目**：升序数组旋转后（无重复元素），O(log n) 找最小值。`[3,4,5,1,2]` → 1。

#### 💡 思路（白话）

- 最小值是「断崖」的谷底。用 `nums[mid]` 和 **`nums[right]`** 比较：
  - `nums[mid] > nums[right]` → 断崖在 mid 右边（mid 在高坡上），`left = mid + 1`；
  - `nums[mid] < nums[right]` → mid 到 right 是平滑上升的，最小值在 mid 或更左，`right = mid`（注意 mid 自己可能就是答案，不能减一）。
- 为什么跟 right 比而不是 left？跟 right 比，两种情况能明确二选一；跟 left 比在「没旋转」的情况下会判断错。

#### ☕ Java

```java
class Solution {
    public int findMin(int[] nums) {
        int left = 0, right = nums.length - 1;
        while (left < right) {              // 注意：< 而不是 <=
            int mid = left + (right - left) / 2;
            if (nums[mid] > nums[right]) left = mid + 1; // 谷底在右
            else right = mid;                            // mid 可能是谷底
        }
        return nums[left];
    }
}
```

#### 🐍 Python

```python
class Solution:
    def findMin(self, nums: List[int]) -> int:
        left, right = 0, len(nums) - 1
        while left < right:
            mid = (left + right) // 2
            if nums[mid] > nums[right]:
                left = mid + 1
            else:
                right = mid
        return nums[left]
```

#### ⏱ 复杂度

时间 O(log n)，空间 O(1)。

**小白提示**：这题用的是另一种二分形态：「左闭右闭 + `while left < right` + `right = mid`」，区间收缩到一个点就是答案。和模板一的区别（`<=`、`mid±1`）务必分清，混用会死循环。
'''},

{"cat": "binary-search", "lc": 4, "t": "寻找两个正序数组的中位数", "d": "困难", "slug": "median-of-two-sorted-arrays", "md": r'''
**题目**：两个有序数组，求合并后的中位数，要求 O(log(m+n))。

#### 💡 思路（白话）

- 转化为更通用的问题：**求两个有序数组中第 k 小的数**（中位数 = 第 (m+n+1)/2 和 (m+n+2)/2 小的数的平均，奇数长度时两者相同）。
- 求第 k 小的「二分淘汰法」：
  - 比较两个数组的**第 k/2 个**元素，较小的那一方的前 k/2 个数**绝不可能**是第 k 小（它们前面最多只有 k-2 个数），整段淘汰；
  - k 减去淘汰个数，继续，直到 k=1（取两数组头部较小者）或一个数组空了（直接在另一个里取）。
- 每轮淘汰 k/2 个，O(log k)。

#### ☕ Java

```java
class Solution {
    public double findMedianSortedArrays(int[] nums1, int[] nums2) {
        int total = nums1.length + nums2.length;
        int k1 = (total + 1) / 2, k2 = (total + 2) / 2;  // 奇数时两者相同
        return (kth(nums1, 0, nums2, 0, k1) + kth(nums1, 0, nums2, 0, k2)) / 2.0;
    }
    // 求 nums1[i..] 和 nums2[j..] 合并后第 k 小
    private int kth(int[] a, int i, int[] b, int j, int k) {
        if (i >= a.length) return b[j + k - 1];     // a 用完了
        if (j >= b.length) return a[i + k - 1];
        if (k == 1) return Math.min(a[i], b[j]);
        int half = k / 2;
        int va = (i + half - 1 < a.length) ? a[i + half - 1] : Integer.MAX_VALUE;
        int vb = (j + half - 1 < b.length) ? b[j + half - 1] : Integer.MAX_VALUE;
        if (va < vb) return kth(a, i + half, b, j, k - half);  // 淘汰 a 的前 half 个
        else         return kth(a, i, b, j + half, k - half);
    }
}
```

#### 🐍 Python

```python
class Solution:
    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:
        def kth(a, i, b, j, k):
            if i >= len(a): return b[j + k - 1]
            if j >= len(b): return a[i + k - 1]
            if k == 1: return min(a[i], b[j])
            half = k // 2
            va = a[i + half - 1] if i + half - 1 < len(a) else float('inf')
            vb = b[j + half - 1] if j + half - 1 < len(b) else float('inf')
            if va < vb:
                return kth(a, i + half, b, j, k - half)
            return kth(a, i, b, j + half, k - half)
        total = len(nums1) + len(nums2)
        k1, k2 = (total + 1) // 2, (total + 2) // 2
        return (kth(nums1, 0, nums2, 0, k1) + kth(nums1, 0, nums2, 0, k2)) / 2
```

#### ⏱ 复杂度

时间 O(log(m+n))，空间 O(log(m+n))（递归）。

**小白提示**：Hot 100 里最难的二分题，第一遍看不懂很正常。先记住核心一句：「**比较两数组第 k/2 个元素，小的那边前 k/2 个整段淘汰**」。面试退而求其次的答案：归并到第 k 个停下，O(m+n)，也能拿大部分分。
'''},
]
