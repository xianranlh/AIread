# LeetCode Hot 100 讲义 · Part 7：动态规划(10) + 多维动态规划(5) + 技巧(5)
PROBLEMS = [
{"cat": "dp", "lc": 70, "t": "爬楼梯", "d": "简单", "slug": "climbing-stairs", "md": r'''
**题目**：爬 n 阶楼梯，每次可以爬 1 或 2 阶，有多少种爬法？

#### 💡 思路（白话）

- DP 四步走的第一次实战：
  1. **状态**：`dp[i]` = 爬到第 i 阶的方法数；
  2. **转移**：最后一步要么跨 1 阶（从 i-1 来）要么跨 2 阶（从 i-2 来），所以 `dp[i] = dp[i-1] + dp[i-2]`（就是斐波那契！）；
  3. **初始**：`dp[1] = 1, dp[2] = 2`；
  4. **顺序**：从小到大。
- 只依赖前两项 → 两个变量滚动，O(1) 空间。

#### ☕ Java

```java
class Solution {
    public int climbStairs(int n) {
        if (n <= 2) return n;
        int prev2 = 1, prev1 = 2;       // dp[1], dp[2]
        for (int i = 3; i <= n; i++) {
            int cur = prev1 + prev2;
            prev2 = prev1;
            prev1 = cur;
        }
        return prev1;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def climbStairs(self, n: int) -> int:
        a, b = 1, 1          # dp[0], dp[1]
        for _ in range(n - 1):
            a, b = b, a + b
        return b
```

#### ⏱ 复杂度

时间 O(n)，空间 O(1)。

**小白提示**：理解转移方程的姿势：**站在终点往回看最后一步**——「我是从哪来的？」所有来源的方法数加起来就是我的方法数。这个「往回看一步」的思维适用于绝大多数 DP。
'''},

{"cat": "dp", "lc": 118, "t": "杨辉三角", "d": "简单", "slug": "pascals-triangle", "md": r'''
**题目**：生成杨辉三角的前 n 行（每个数是它上方两数之和）。

#### 💡 思路（白话）

- 规则直接翻译成代码：
  - 每行第一个和最后一个是 1；
  - 中间的 `row[j] = 上一行[j-1] + 上一行[j]`。
- 这其实就是一个最直观的二维 DP：状态是「第 i 行第 j 个」，转移靠上一行——当热身题，找「用旧行算新行」的感觉。

#### ☕ Java

```java
class Solution {
    public List<List<Integer>> generate(int numRows) {
        List<List<Integer>> res = new ArrayList<>();
        for (int i = 0; i < numRows; i++) {
            List<Integer> row = new ArrayList<>();
            for (int j = 0; j <= i; j++) {
                if (j == 0 || j == i) row.add(1);                 // 两端是 1
                else row.add(res.get(i - 1).get(j - 1) + res.get(i - 1).get(j));
            }
            res.add(row);
        }
        return res;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def generate(self, numRows: int) -> List[List[int]]:
        res = []
        for i in range(numRows):
            row = [1] * (i + 1)
            for j in range(1, i):
                row[j] = res[-1][j - 1] + res[-1][j]
            res.append(row)
        return res
```

#### ⏱ 复杂度

时间 O(n²)，空间 O(1)（不算结果）。

**小白提示**：Python 版「先全填 1 再改中间」比逐个判断两端更顺手。这题没难度，价值在于体验「逐行构建、新行依赖旧行」——后面的多维 DP 都是这个节奏。
'''},

{"cat": "dp", "lc": 198, "t": "打家劫舍", "d": "中等", "slug": "house-robber", "md": r'''
**题目**：沿街房屋各有现金，**不能偷相邻两家**，求能偷到的最大金额。

**举例**：`[2,7,9,3,1]` → 偷 2+9+1 = 12。

#### 💡 思路（白话）

- **状态**：`dp[i]` = 只考虑前 i 间房能偷到的最大金额。
- **转移**：第 i 间房偷不偷？
  - 偷：拿 `nums[i]`，但 i-1 不能偷 → `dp[i-2] + nums[i]`；
  - 不偷：→ `dp[i-1]`；
  - 取大者：`dp[i] = max(dp[i-1], dp[i-2] + nums[i])`。
- **初始**：`dp[0] = nums[0]`，`dp[1] = max(nums[0], nums[1])`。
- 又是只依赖前两项 → 滚动变量。

#### ☕ Java

```java
class Solution {
    public int rob(int[] nums) {
        int prev2 = 0, prev1 = 0;   // dp[i-2], dp[i-1]（前面补 0 间房，初始都是 0）
        for (int x : nums) {
            int cur = Math.max(prev1, prev2 + x);  // 不偷 vs 偷
            prev2 = prev1;
            prev1 = cur;
        }
        return prev1;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def rob(self, nums: List[int]) -> int:
        prev2 = prev1 = 0
        for x in nums:
            prev2, prev1 = prev1, max(prev1, prev2 + x)
        return prev1
```

#### ⏱ 复杂度

时间 O(n)，空间 O(1)。

**小白提示**：「**选 or 不选**」是 DP 最经典的二分支结构，无数题都是它：打家劫舍、背包、股票……从 0 开始滚动（想象前面有 0 间房）可以避开下标边界判断，代码更干净。
'''},

{"cat": "dp", "lc": 279, "t": "完全平方数", "d": "中等", "slug": "perfect-squares", "md": r'''
**题目**：求和为 n 的完全平方数（1, 4, 9, 16…）的**最少数量**。如 12 = 4+4+4 → 3。

#### 💡 思路（白话）

- 这是「**完全背包**」模型：物品 = 各个平方数（可无限用），背包容量 = n，求装满的最少件数。
- **状态**：`dp[i]` = 凑出 i 最少要几个平方数。
- **转移**：最后一个用的平方数是 `j*j`，那么 `dp[i] = min(dp[i - j*j] + 1)`，枚举所有 `j*j <= i`。
- **初始**：`dp[0] = 0`，其余设为无穷大。

#### ☕ Java

```java
class Solution {
    public int numSquares(int n) {
        int[] dp = new int[n + 1];
        Arrays.fill(dp, Integer.MAX_VALUE);
        dp[0] = 0;
        for (int i = 1; i <= n; i++) {
            for (int j = 1; j * j <= i; j++) {
                dp[i] = Math.min(dp[i], dp[i - j * j] + 1);
            }
        }
        return dp[n];
    }
}
```

#### 🐍 Python

```python
class Solution:
    def numSquares(self, n: int) -> int:
        dp = [0] + [float('inf')] * n
        for i in range(1, n + 1):
            j = 1
            while j * j <= i:
                dp[i] = min(dp[i], dp[i - j * j] + 1)
                j += 1
        return int(dp[n])
```

#### ⏱ 复杂度

时间 O(n√n)，空间 O(n)。

**小白提示**：和下一题「零钱兑换」是同一个模型（把「平方数」换成「硬币面额」），两题对照着写，背包的感觉就出来了。`dp[0] = 0` 是地基：「凑出 0 需要 0 个」。
'''},

{"cat": "dp", "lc": 322, "t": "零钱兑换", "d": "中等", "slug": "coin-change", "md": r'''
**题目**：给硬币面额（每种无限个）和总金额，求凑出总额的**最少硬币数**；凑不出返回 -1。

**举例**：`coins = [1,2,5], amount = 11` → 5+5+1，返回 3。

#### 💡 思路（白话）

- 完全背包求「最少件数」的代表题：
  - **状态**：`dp[i]` = 凑出金额 i 的最少硬币数；
  - **转移**：最后一枚硬币是哪种？`dp[i] = min(dp[i - coin] + 1)`，遍历所有面额；
  - **初始**：`dp[0] = 0`，其余无穷大（表示「暂时凑不出」）。
- 最后 `dp[amount]` 还是无穷大 → 凑不出，返回 -1。
- 为什么不能贪心（先用大面额）？反例：`coins=[1,3,4], amount=6`，贪心 4+1+1=3 枚，正解 3+3=2 枚。

#### ☕ Java

```java
class Solution {
    public int coinChange(int[] coins, int amount) {
        int[] dp = new int[amount + 1];
        Arrays.fill(dp, amount + 1);     // 用 amount+1 当「无穷大」，防溢出
        dp[0] = 0;
        for (int i = 1; i <= amount; i++) {
            for (int coin : coins) {
                if (coin <= i)
                    dp[i] = Math.min(dp[i], dp[i - coin] + 1);
            }
        }
        return dp[amount] > amount ? -1 : dp[amount];
    }
}
```

#### 🐍 Python

```python
class Solution:
    def coinChange(self, coins: List[int], amount: int) -> int:
        dp = [0] + [float('inf')] * amount
        for i in range(1, amount + 1):
            for coin in coins:
                if coin <= i:
                    dp[i] = min(dp[i], dp[i - coin] + 1)
        return -1 if dp[amount] == float('inf') else dp[amount]
```

#### ⏱ 复杂度

时间 O(amount × 硬币种数)，空间 O(amount)。

**小白提示**：DP 面试第一高频题。Java 用 `amount+1` 代替 `Integer.MAX_VALUE` 当无穷大，避免 `+1` 溢出成负数——这个细节常被问。面试记得主动说出「贪心为什么不行」的反例。
'''},

{"cat": "dp", "lc": 139, "t": "单词拆分", "d": "中等", "slug": "word-break", "md": r'''
**题目**：判断字符串 s 能否被拆分成若干个字典中的单词（单词可重复使用）。

**举例**：`s = "leetcode", wordDict = ["leet","code"]` → true。

#### 💡 思路（白话）

- **状态**：`dp[i]` = s 的前 i 个字符能否被拆分（布尔值）。
- **转移**：枚举最后一个单词的起点 j：如果 `dp[j]` 为 true（前 j 个拆得开）且 `s[j..i)` 在字典里，则 `dp[i] = true`。
- **初始**：`dp[0] = true`（空串算拆分成功）。
- 本质也是完全背包：物品是单词（可重复用），背包是字符串，只是「装」必须按顺序拼接。

#### ☕ Java

```java
class Solution {
    public boolean wordBreak(String s, List<String> wordDict) {
        Set<String> dict = new HashSet<>(wordDict);   // 转 set 加速查询
        boolean[] dp = new boolean[s.length() + 1];
        dp[0] = true;
        for (int i = 1; i <= s.length(); i++) {
            for (int j = 0; j < i; j++) {
                if (dp[j] && dict.contains(s.substring(j, i))) {
                    dp[i] = true;
                    break;                            // 找到一种拆法就够了
                }
            }
        }
        return dp[s.length()];
    }
}
```

#### 🐍 Python

```python
class Solution:
    def wordBreak(self, s: str, wordDict: List[str]) -> bool:
        words = set(wordDict)
        dp = [True] + [False] * len(s)
        for i in range(1, len(s) + 1):
            for j in range(i):
                if dp[j] and s[j:i] in words:
                    dp[i] = True
                    break
        return dp[-1]
```

#### ⏱ 复杂度

时间 O(n² × 单词比较)，空间 O(n)。

**小白提示**：字符串 DP 的下标约定：「`dp[i]` 对应**前 i 个字符**（即 `s[0..i)`）」，比「以 i 结尾」少很多 off-by-one 错误，建议养成习惯。
'''},

{"cat": "dp", "lc": 300, "t": "最长递增子序列", "d": "中等", "slug": "longest-increasing-subsequence", "md": r'''
**题目**：求数组中最长**严格递增子序列**（可以不连续）的长度。

**举例**：`[10,9,2,5,3,7,101,18]` → `[2,3,7,101]`，返回 4。

#### 💡 思路（白话）

- **状态**：`dp[i]` = **以 nums[i] 结尾**的最长递增子序列长度（注意「以 i 结尾」，否则没法转移）。
- **转移**：往前找所有比我小的 `nums[j]`，接在它后面：`dp[i] = max(dp[j]) + 1`（`j < i` 且 `nums[j] < nums[i]`）。
- **答案**：所有 `dp[i]` 的最大值（最长的序列不一定以最后一个元素结尾）。
- O(n²) 必须会；O(n log n) 的「贪心 + 二分」（维护一个 tails 数组）作为进阶。

#### ☕ Java

```java
class Solution {
    public int lengthOfLIS(int[] nums) {
        int[] dp = new int[nums.length];
        Arrays.fill(dp, 1);                 // 自己单独成序列，长度 1
        int best = 1;
        for (int i = 1; i < nums.length; i++) {
            for (int j = 0; j < i; j++) {
                if (nums[j] < nums[i])
                    dp[i] = Math.max(dp[i], dp[j] + 1);
            }
            best = Math.max(best, dp[i]);
        }
        return best;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def lengthOfLIS(self, nums: List[int]) -> int:
        tails = []                     # O(n log n)：tails[k] = 长度 k+1 的递增序列的最小结尾
        for x in nums:
            i = bisect_left(tails, x)
            if i == len(tails):
                tails.append(x)        # x 比所有结尾都大，序列变长
            else:
                tails[i] = x           # 替换：让结尾更小、后续更有潜力
        return len(tails)
```

#### ⏱ 复杂度

DP 法 O(n²)；二分法 O(n log n)。空间 O(n)。

**小白提示**：「以 i 结尾」的状态定义是序列 DP 的标准姿势——不带这个限定就无法知道「能不能接上」。二分法里 tails 不是真实序列，只是「各长度的最小结尾」，能答出这点是面试亮点。
'''},

{"cat": "dp", "lc": 152, "t": "乘积最大子数组", "d": "中等", "slug": "maximum-product-subarray", "md": r'''
**题目**：找出乘积最大的**连续**子数组，返回乘积。

**举例**：`[2,3,-2,4]` → `[2,3]`，返回 6。

#### 💡 思路（白话）

- 和「最大子数组和」像，但乘法有个魔鬼：**负负得正**——当前的最小值乘个负数可能瞬间变最大！
- 所以要同时维护两个量：以 i 结尾的**最大**乘积 `maxP` 和**最小**乘积 `minP`。
- 转移：新元素 x 有三个候选：`x` 自己、`maxP * x`、`minP * x`，最大者给 maxP、最小者给 minP。
- 实用小技巧：x 为负时先把 maxP 和 minP 交换，再按「最大子数组和」的方式写。

#### ☕ Java

```java
class Solution {
    public int maxProduct(int[] nums) {
        int maxP = nums[0], minP = nums[0], best = nums[0];
        for (int i = 1; i < nums.length; i++) {
            int x = nums[i];
            if (x < 0) {                 // 负数让最大最小互换
                int t = maxP; maxP = minP; minP = t;
            }
            maxP = Math.max(x, maxP * x);
            minP = Math.min(x, minP * x);
            best = Math.max(best, maxP);
        }
        return best;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def maxProduct(self, nums: List[int]) -> int:
        max_p = min_p = best = nums[0]
        for x in nums[1:]:
            if x < 0:
                max_p, min_p = min_p, max_p
            max_p = max(x, max_p * x)
            min_p = min(x, min_p * x)
            best = max(best, max_p)
        return best
```

#### ⏱ 复杂度

时间 O(n)，空间 O(1)。

**小白提示**：本题教会你一个重要思想：**当转移需要的信息不够时，多维护一个状态**（这里是同时记最大和最小）。遇到「带负数的乘积」条件反射想到这招。
'''},

{"cat": "dp", "lc": 416, "t": "分割等和子集", "d": "中等", "slug": "partition-equal-subset-sum", "md": r'''
**题目**：能否把数组分成两个和相等的子集？

**举例**：`[1,5,11,5]` → true（[1,5,5] 和 [11]）。

#### 💡 思路（白话）

- 转化：两子集和相等 ⇔ **能否选出一些数，和恰好等于总和的一半** `target = sum/2`（sum 是奇数直接 false）。
- 这是 **0-1 背包**（每个数只能用一次）：
  - **状态**：`dp[j]` = 能否凑出和 j（布尔）；
  - **转移**：对每个数 x：`dp[j] = dp[j] || dp[j - x]`；
  - **关键**：j 要**从大到小**遍历！从小到大会让同一个 x 被用多次（变成完全背包）。
- **初始**：`dp[0] = true`。

#### ☕ Java

```java
class Solution {
    public boolean canPartition(int[] nums) {
        int sum = Arrays.stream(nums).sum();
        if (sum % 2 != 0) return false;
        int target = sum / 2;
        boolean[] dp = new boolean[target + 1];
        dp[0] = true;
        for (int x : nums) {
            for (int j = target; j >= x; j--) {   // 0-1 背包：倒序！
                dp[j] = dp[j] || dp[j - x];
            }
        }
        return dp[target];
    }
}
```

#### 🐍 Python

```python
class Solution:
    def canPartition(self, nums: List[int]) -> bool:
        total = sum(nums)
        if total % 2:
            return False
        target = total // 2
        dp = [True] + [False] * target
        for x in nums:
            for j in range(target, x - 1, -1):   # 倒序
                dp[j] = dp[j] or dp[j - x]
        return dp[target]
```

#### ⏱ 复杂度

时间 O(n × target)，空间 O(target)。

**小白提示**：背包终极口诀：「**0-1 背包倒序遍历容量，完全背包正序遍历容量**」。为什么倒序？正序时 `dp[j-x]` 可能已经被本轮的 x 更新过，等于一个数用了两次。这句话面试必考。
'''},

{"cat": "dp", "lc": 32, "t": "最长有效括号", "d": "困难", "slug": "longest-valid-parentheses", "md": r'''
**题目**：求只含 `(` 和 `)` 的字符串中，最长**有效（正确闭合）**括号子串的长度。

**举例**：`")()())"` → `"()()"`，返回 4。

#### 💡 思路（白话）

- 栈法（最好懂）：栈里存**下标**。
  - 先压入 -1 当「参照物」（最后一个无法匹配的位置）；
  - 遇 `(`：下标入栈；
  - 遇 `)`：弹栈（配对掉一个 `(`）。弹完后：
    - 栈空了 → 这个 `)` 多余，把它的下标压入当新参照物；
    - 栈不空 → 当前有效长度 = `i - 栈顶`，更新答案。
- 「栈底永远是『最后一个不可匹配位置』」——有效子串只能从它后面开始算。

#### ☕ Java

```java
class Solution {
    public int longestValidParentheses(String s) {
        Deque<Integer> stack = new ArrayDeque<>();
        stack.push(-1);                       // 参照物
        int best = 0;
        for (int i = 0; i < s.length(); i++) {
            if (s.charAt(i) == '(') {
                stack.push(i);
            } else {
                stack.pop();
                if (stack.isEmpty()) {
                    stack.push(i);            // 新参照物
                } else {
                    best = Math.max(best, i - stack.peek());
                }
            }
        }
        return best;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def longestValidParentheses(self, s: str) -> int:
        stack, best = [-1], 0
        for i, c in enumerate(s):
            if c == '(':
                stack.append(i)
            else:
                stack.pop()
                if not stack:
                    stack.append(i)
                else:
                    best = max(best, i - stack[-1])
        return best
```

#### ⏱ 复杂度

时间 O(n)，空间 O(n)。

**小白提示**：拿 `")()())"` 在纸上模拟一遍栈的变化（特别注意 -1 和新参照物的作用）。纯 DP 解法也存在但更绕，面试用栈法讲清楚足够了。
'''},

{"cat": "multi-dp", "lc": 62, "t": "不同路径", "d": "中等", "slug": "unique-paths", "md": r'''
**题目**：机器人从 m×n 网格左上角出发，每次只能**向右或向下**，到右下角共有多少条路径？

#### 💡 思路（白话）

- 二维 DP 入门：
  - **状态**：`dp[i][j]` = 到达 (i,j) 的路径数；
  - **转移**：只能从上面或左面来 → `dp[i][j] = dp[i-1][j] + dp[i][j-1]`；
  - **初始**：第一行、第一列全是 1（只有一条直路）。
- 空间优化：逐行计算时只需要上一行 → 一维数组滚动：`dp[j] += dp[j-1]`（dp[j] 是上方的旧值，dp[j-1] 是左方的新值）。

#### ☕ Java

```java
class Solution {
    public int uniquePaths(int m, int n) {
        int[] dp = new int[n];
        Arrays.fill(dp, 1);              // 第一行全 1
        for (int i = 1; i < m; i++) {
            for (int j = 1; j < n; j++) {
                dp[j] += dp[j - 1];      // 上方(旧dp[j]) + 左方(新dp[j-1])
            }
        }
        return dp[n - 1];
    }
}
```

#### 🐍 Python

```python
class Solution:
    def uniquePaths(self, m: int, n: int) -> int:
        dp = [1] * n
        for _ in range(1, m):
            for j in range(1, n):
                dp[j] += dp[j - 1]
        return dp[-1]
```

#### ⏱ 复杂度

时间 O(mn)，空间 O(n)。

**小白提示**：先写二维版本（好理解），再练一维滚动优化（面试加分）。在纸上画 3×3 表格手动填一遍，「上+左」的转移立刻直观。数学解法 C(m+n-2, m-1) 可当谈资。
'''},

{"cat": "multi-dp", "lc": 64, "t": "最小路径和", "d": "中等", "slug": "minimum-path-sum", "md": r'''
**题目**：网格每格有一个非负数，从左上到右下（只能右/下走），求经过数字总和的最小值。

#### 💡 思路（白话）

- 「不同路径」的兄弟题，把「求方案数（加法）」换成「求最小值（min）」：
  - `dp[i][j] = grid[i][j] + min(dp[i-1][j], dp[i][j-1])`；
  - 第一行只能从左来（累加），第一列只能从上来（累加）。
- 可以直接在 grid 上原地改（省空间），也可以一维滚动。

#### ☕ Java

```java
class Solution {
    public int minPathSum(int[][] grid) {
        int m = grid.length, n = grid[0].length;
        for (int i = 0; i < m; i++) {
            for (int j = 0; j < n; j++) {
                if (i == 0 && j == 0) continue;
                else if (i == 0) grid[i][j] += grid[i][j - 1];      // 第一行
                else if (j == 0) grid[i][j] += grid[i - 1][j];      // 第一列
                else grid[i][j] += Math.min(grid[i - 1][j], grid[i][j - 1]);
            }
        }
        return grid[m - 1][n - 1];
    }
}
```

#### 🐍 Python

```python
class Solution:
    def minPathSum(self, grid: List[List[int]]) -> int:
        m, n = len(grid), len(grid[0])
        for i in range(m):
            for j in range(n):
                if i == 0 and j == 0:
                    continue
                elif i == 0:
                    grid[i][j] += grid[i][j - 1]
                elif j == 0:
                    grid[i][j] += grid[i - 1][j]
                else:
                    grid[i][j] += min(grid[i - 1][j], grid[i][j - 1])
        return grid[-1][-1]
```

#### ⏱ 复杂度

时间 O(mn)，空间 O(1)（原地修改）。

**小白提示**：网格 DP 三连问：从哪来（上/左）？怎么合（加/min/max）？边界怎么填（第一行第一列单独处理）？回答完这三问，代码自然就出来了。
'''},

{"cat": "multi-dp", "lc": 5, "t": "最长回文子串", "d": "中等", "slug": "longest-palindromic-substring", "md": r'''
**题目**：找出字符串中最长的回文子串。`"babad"` → `"bab"`（或 `"aba"`）。

#### 💡 思路（白话）

- **中心扩展法**（最直观，推荐）：回文有个中心，从中心向两边扩，两边字符相等就继续。
- 中心有两种：**单字符中心**（奇数长回文，如 aba）和**双字符中心**（偶数长，如 abba）。每个位置都试这两种，共 2n-1 个中心。
- 写个辅助函数 `expand(l, r)`：从 l、r 向外扩到不能扩，返回回文边界。

#### ☕ Java

```java
class Solution {
    private int start = 0, maxLen = 1;

    public String longestPalindrome(String s) {
        for (int i = 0; i < s.length(); i++) {
            expand(s, i, i);       // 奇数长度，中心是 i
            expand(s, i, i + 1);   // 偶数长度，中心是 i,i+1 之间
        }
        return s.substring(start, start + maxLen);
    }
    private void expand(String s, int l, int r) {
        while (l >= 0 && r < s.length() && s.charAt(l) == s.charAt(r)) {
            l--; r++;
        }
        // 此时 [l+1, r-1] 是回文
        if (r - l - 1 > maxLen) {
            maxLen = r - l - 1;
            start = l + 1;
        }
    }
}
```

#### 🐍 Python

```python
class Solution:
    def longestPalindrome(self, s: str) -> str:
        def expand(l, r):
            while l >= 0 and r < len(s) and s[l] == s[r]:
                l -= 1; r += 1
            return l + 1, r - 1          # 回文区间
        start, end = 0, 0
        for i in range(len(s)):
            for l, r in (expand(i, i), expand(i, i + 1)):
                if r - l > end - start:
                    start, end = l, r
        return s[start:end + 1]
```

#### ⏱ 复杂度

时间 O(n²)，空间 O(1)。

**小白提示**：循环退出时 l、r 已经**多走了一步**，所以回文是 `[l+1, r-1]`、长度是 `r-l-1`——这里最容易算错。区间 DP 解法（`dp[i][j]` 表示 s[i..j] 是否回文）也要了解，是「区间型 DP」的代表。
'''},

{"cat": "multi-dp", "lc": 1143, "t": "最长公共子序列", "d": "中等", "slug": "longest-common-subsequence", "md": r'''
**题目**：求两个字符串的最长公共**子序列**（可以不连续，顺序不变）长度。`"abcde"` 和 `"ace"` → 3。

#### 💡 思路（白话）

- 双字符串 DP 的标准范式：
  - **状态**：`dp[i][j]` = text1 前 i 个字符与 text2 前 j 个字符的 LCS 长度；
  - **转移**（看两串的当前末尾字符）：
    - `text1[i-1] == text2[j-1]` → 这个字符必入选：`dp[i][j] = dp[i-1][j-1] + 1`；
    - 不等 → 至少有一个末尾用不上，扔谁？都试试：`dp[i][j] = max(dp[i-1][j], dp[i][j-1])`；
  - **初始**：第 0 行第 0 列全 0（空串和谁的 LCS 都是 0）。

#### ☕ Java

```java
class Solution {
    public int longestCommonSubsequence(String text1, String text2) {
        int m = text1.length(), n = text2.length();
        int[][] dp = new int[m + 1][n + 1];
        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                if (text1.charAt(i - 1) == text2.charAt(j - 1))
                    dp[i][j] = dp[i - 1][j - 1] + 1;     // 末尾字符相同
                else
                    dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
        return dp[m][n];
    }
}
```

#### 🐍 Python

```python
class Solution:
    def longestCommonSubsequence(self, text1: str, text2: str) -> int:
        m, n = len(text1), len(text2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if text1[i - 1] == text2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
        return dp[m][n]
```

#### ⏱ 复杂度

时间 O(mn)，空间 O(mn)。

**小白提示**：双字符串 DP 的固定开局：「**dp 开 (m+1)×(n+1)，多出的第 0 行/列代表空串**」，下标 `dp[i][j]` 对应字符 `[i-1]`、`[j-1]`。拿 "abcde"/"ace" 画一张 6×4 的表手填一遍，编辑距离也就会了。
'''},

{"cat": "multi-dp", "lc": 72, "t": "编辑距离", "d": "困难", "slug": "edit-distance", "md": r'''
**题目**：求把 word1 变成 word2 的最少操作数（可插入、删除、替换一个字符）。`"horse"` → `"ros"` 需要 3 步。

#### 💡 思路（白话）

- **状态**：`dp[i][j]` = word1 前 i 个字符变成 word2 前 j 个字符的最少操作数。
- **转移**（还是看两端末尾）：
  - 末尾相同 → 不用动：`dp[i][j] = dp[i-1][j-1]`；
  - 不同 → 三种操作选最便宜的，各对应一个子问题：
    - **替换**：`dp[i-1][j-1] + 1`（把 word1 末尾换成 word2 末尾）；
    - **删除**：`dp[i-1][j] + 1`（删掉 word1 末尾）；
    - **插入**：`dp[i][j-1] + 1`（往 word1 末尾插一个 word2 的末尾字符）。
- **初始**：`dp[i][0] = i`（全删）、`dp[0][j] = j`（全插）。

#### ☕ Java

```java
class Solution {
    public int minDistance(String word1, String word2) {
        int m = word1.length(), n = word2.length();
        int[][] dp = new int[m + 1][n + 1];
        for (int i = 0; i <= m; i++) dp[i][0] = i;   // 全删
        for (int j = 0; j <= n; j++) dp[0][j] = j;   // 全插
        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                if (word1.charAt(i - 1) == word2.charAt(j - 1))
                    dp[i][j] = dp[i - 1][j - 1];
                else
                    dp[i][j] = 1 + Math.min(dp[i - 1][j - 1],          // 替换
                                Math.min(dp[i - 1][j], dp[i][j - 1])); // 删除 / 插入
            }
        }
        return dp[m][n];
    }
}
```

#### 🐍 Python

```python
class Solution:
    def minDistance(self, word1: str, word2: str) -> int:
        m, n = len(word1), len(word2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m + 1): dp[i][0] = i
        for j in range(n + 1): dp[0][j] = j
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if word1[i - 1] == word2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = 1 + min(dp[i - 1][j - 1], dp[i - 1][j], dp[i][j - 1])
        return dp[m][n]
```

#### ⏱ 复杂度

时间 O(mn)，空间 O(mn)。

**小白提示**：和 LCS 是同一张「双字符串 DP」皮，区别只在转移：LCS 取 max、编辑距离取 min+1。记住三个方向的含义：「左上=替换、上=删、左=插」。这个算法在拼写纠错、DNA 比对里是真实生产力。
'''},

{"cat": "tricks", "lc": 136, "t": "只出现一次的数字", "d": "简单", "slug": "single-number", "md": r'''
**题目**：数组中除一个元素只出现一次外，其余都出现两次。找出那个数，要求 O(n) 时间、O(1) 空间。

#### 💡 思路（白话）

- **异或（XOR, `^`）三条性质**：
  1. `a ^ a = 0`（自己消自己）；
  2. `a ^ 0 = a`；
  3. 满足交换律、结合律（顺序随便换）。
- 把所有数全部异或起来：出现两次的两两相消变成 0，剩下的就是只出现一次的那个。

#### ☕ Java

```java
class Solution {
    public int singleNumber(int[] nums) {
        int res = 0;
        for (int x : nums) res ^= x;    // 成对的相消
        return res;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def singleNumber(self, nums: List[int]) -> int:
        res = 0
        for x in nums:
            res ^= x
        return res
```

#### ⏱ 复杂度

时间 O(n)，空间 O(1)。

**小白提示**：位运算第一课。XOR 的「成对相消」还能玩出很多花：交换两个变量、找缺失数字、找两个落单的数（进阶题 260）。把那三条性质背熟。
'''},

{"cat": "tricks", "lc": 169, "t": "多数元素", "d": "简单", "slug": "majority-element", "md": r'''
**题目**：找出数组中出现次数**超过一半**的元素（保证存在），要求 O(n) 时间、O(1) 空间。

#### 💡 思路（白话）

- **摩尔投票**：想象一场混战——不同阵营的人两两同归于尽，因为多数派人数超过一半，**最后站着的一定是多数派**。
- 实现：维护 `candidate`（当前候选人）和 `count`（它的「血量」）：
  - `count == 0` → 换当前元素当候选人；
  - 元素 == 候选人 → `count++`，否则 `count--`（互相抵消）。

#### ☕ Java

```java
class Solution {
    public int majorityElement(int[] nums) {
        int candidate = nums[0], count = 0;
        for (int x : nums) {
            if (count == 0) candidate = x;   // 换候选人
            count += (x == candidate) ? 1 : -1;
        }
        return candidate;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def majorityElement(self, nums: List[int]) -> int:
        candidate, count = nums[0], 0
        for x in nums:
            if count == 0:
                candidate = x
            count += 1 if x == candidate else -1
        return candidate
```

#### ⏱ 复杂度

时间 O(n)，空间 O(1)。

**小白提示**：如果题目**不保证**多数元素存在，最后要再扫一遍验证 candidate 的真实票数。哈希表计数、排序取中间也都对，但摩尔投票的 O(1) 空间是面试想听到的。
'''},

{"cat": "tricks", "lc": 75, "t": "颜色分类", "d": "中等", "slug": "sort-colors", "md": r'''
**题目**：数组只含 0、1、2（红白蓝），原地排序，要求一趟扫描、O(1) 空间。

#### 💡 思路（白话）

- **荷兰国旗问题**，三指针：
  - `p0`：0 区的右边界（p0 左边全是 0）；
  - `p2`：2 区的左边界（p2 右边全是 2）；
  - `i`：当前考察的位置。
- 规则：`nums[i]` 是 0 → 和 p0 交换，p0++、i++；是 2 → 和 p2 交换，p2--，**i 不动**（换过来的还没看过！）；是 1 → i++。
- 直到 `i > p2`（中间区处理完）。

#### ☕ Java

```java
class Solution {
    public void sortColors(int[] nums) {
        int p0 = 0, i = 0, p2 = nums.length - 1;
        while (i <= p2) {
            if (nums[i] == 0) {
                swap(nums, i++, p0++);
            } else if (nums[i] == 2) {
                swap(nums, i, p2--);   // i 不动：换来的数还没检查
            } else {
                i++;
            }
        }
    }
    private void swap(int[] a, int i, int j) {
        int t = a[i]; a[i] = a[j]; a[j] = t;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def sortColors(self, nums: List[int]) -> None:
        p0, i, p2 = 0, 0, len(nums) - 1
        while i <= p2:
            if nums[i] == 0:
                nums[i], nums[p0] = nums[p0], nums[i]
                p0 += 1; i += 1
            elif nums[i] == 2:
                nums[i], nums[p2] = nums[p2], nums[i]
                p2 -= 1               # i 不动
            else:
                i += 1
        return None
```

#### ⏱ 复杂度

时间 O(n)，空间 O(1)。

**小白提示**：两个细节决定成败：① 和 p2 换完 **i 不能加**（右边换来的数没检查过）；② 和 p0 换完 i 可以加（p0 位置只可能是 0 或 1，换来的 1 不用再处理）。这个「三路分区」也是快排优化（三向切分）的核心。
'''},

{"cat": "tricks", "lc": 31, "t": "下一个排列", "d": "中等", "slug": "next-permutation", "md": r'''
**题目**：求数组在字典序中的**下一个**排列（已是最大则变成最小），原地修改。

**举例**：`[1,2,3]` → `[1,3,2]`；`[3,2,1]` → `[1,2,3]`。

#### 💡 思路（白话）

- 想让数字「变大一点点」，三步：
  1. **从右往左**找第一个「升序对」：`nums[i] < nums[i+1]`（i 右边是降序的，已经是最大形态，动它没用，必须动 i）；
  2. 再**从右往左**找第一个比 `nums[i]` 大的数 `nums[j]`（即比它大的数里最小的），**交换**——i 位变大了一点点；
  3. 把 i 右边**整段翻转**（降序→升序，变成最小形态）——保证只大「一点点」。
- 找不到升序对（整个降序）说明已是最大，直接整体翻转。

#### ☕ Java

```java
class Solution {
    public void nextPermutation(int[] nums) {
        int n = nums.length, i = n - 2;
        while (i >= 0 && nums[i] >= nums[i + 1]) i--;   // 1. 找升序对
        if (i >= 0) {
            int j = n - 1;
            while (nums[j] <= nums[i]) j--;             // 2. 找刚好更大的
            int t = nums[i]; nums[i] = nums[j]; nums[j] = t;
        }
        for (int l = i + 1, r = n - 1; l < r; l++, r--) { // 3. 翻转后缀
            int t = nums[l]; nums[l] = nums[r]; nums[r] = t;
        }
    }
}
```

#### 🐍 Python

```python
class Solution:
    def nextPermutation(self, nums: List[int]) -> None:
        n, i = len(nums), len(nums) - 2
        while i >= 0 and nums[i] >= nums[i + 1]:
            i -= 1
        if i >= 0:
            j = n - 1
            while nums[j] <= nums[i]:
                j -= 1
            nums[i], nums[j] = nums[j], nums[i]
        nums[i + 1:] = reversed(nums[i + 1:])
```

#### ⏱ 复杂度

时间 O(n)，空间 O(1)。

**小白提示**：拿 `[1,3,5,4,2]` 在纸上走三步：找到 i=1（3<5）→ 从右找到 4 交换 → `[1,4,5,3,2]` → 翻转后缀 → `[1,4,2,3,5]`。比较时用 `>=`/`<=`（跳过相等）才能正确处理重复元素。
'''},

{"cat": "tricks", "lc": 287, "t": "寻找重复数", "d": "中等", "slug": "find-the-duplicate-number", "md": r'''
**题目**：长度 n+1 的数组，元素都在 1~n 之间，**只有一个数重复**（可能重复多次）。不能修改数组、O(1) 空间找出它。

#### 💡 思路（白话）

- 神转化：把数组看成链表——**下标 i 的「next」是 nums[i]**（值在 1~n，正好是合法下标）。
- 因为有重复值，必然有两个下标指向同一个位置 → 这个「链表」**必有环**，且**环的入口就是重复数**！
- 于是直接套「环形链表 II」（142 题）的 Floyd 判圈：快慢指针相遇 → 一个回起点 → 同速再走 → 相遇点即答案。

#### ☕ Java

```java
class Solution {
    public int findDuplicate(int[] nums) {
        int slow = nums[0], fast = nums[nums[0]];
        while (slow != fast) {            // 第一阶段：找相遇点
            slow = nums[slow];
            fast = nums[nums[fast]];
        }
        slow = 0;                         // 第二阶段：找环入口
        while (slow != fast) {
            slow = nums[slow];
            fast = nums[fast];
        }
        return slow;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def findDuplicate(self, nums: List[int]) -> int:
        slow, fast = nums[0], nums[nums[0]]
        while slow != fast:
            slow = nums[slow]
            fast = nums[nums[fast]]
        slow = 0
        while slow != fast:
            slow = nums[slow]
            fast = nums[fast]
        return slow
```

#### ⏱ 复杂度

时间 O(n)，空间 O(1)。

**小白提示**：拿 `[1,3,4,2,2]` 画一画：0→1→3→2→4→2→4…（2 和 4 成环，入口 2 就是重复数）。Hot 100 的收官题，它把「链表判环」用在了看似不相关的数组题上——**算法学到后面，拼的就是这种转化能力**。刷完这题，恭喜你 Hot 100 通关！🎉
'''},
]
