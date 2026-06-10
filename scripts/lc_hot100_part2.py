# LeetCode Hot 100 讲义 · Part 2：子串(3) + 普通数组(5) + 矩阵(4)
PROBLEMS = [
{"cat": "substring", "lc": 560, "t": "和为 K 的子数组", "d": "中等", "slug": "subarray-sum-equals-k", "md": r'''
**题目**：统计数组中「和恰好等于 k」的**连续**子数组的个数（数组可能有负数）。

**举例**：`nums = [1,1,1], k = 2` → 返回 2（`[1,1]` 出现在两个位置）。

#### 💡 思路（白话）

- 有负数，滑动窗口失效（窗口变大和不一定变大）→ 用**前缀和**。
- 设 `pre[i]` = 前 i 个数的和，则子数组 `(j, i]` 的和 = `pre[i] - pre[j]`。
- 要它等于 k，即 `pre[j] = pre[i] - k`。所以遍历到 i 时只需问：「**前面有几个前缀和等于 `pre[i] - k`？**」——又是哈希表的拿手活（前缀和值 → 出现次数）。
- 初始要放入 `{0: 1}`，代表「空前缀」，否则从头开始的子数组会漏掉。

#### ☕ Java

```java
class Solution {
    public int subarraySum(int[] nums, int k) {
        Map<Integer, Integer> count = new HashMap<>();
        count.put(0, 1);              // 空前缀
        int pre = 0, res = 0;
        for (int x : nums) {
            pre += x;                              // 当前前缀和
            res += count.getOrDefault(pre - k, 0); // 前面有几个 pre-k
            count.merge(pre, 1, Integer::sum);     // 登记当前前缀和
        }
        return res;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def subarraySum(self, nums: List[int], k: int) -> int:
        count = defaultdict(int)
        count[0] = 1
        pre = res = 0
        for x in nums:
            pre += x
            res += count[pre - k]
            count[pre] += 1
        return res
```

#### ⏱ 复杂度

时间 O(n)，空间 O(n)。

**小白提示**：「前缀和 + 哈希表」和「两数之和」是同一个套路：边走边查「我需要的那个值出现过几次」。`count[0]=1` 这个初始化最容易忘，记住它对应「从下标 0 开始的子数组」。
'''},

{"cat": "substring", "lc": 239, "t": "滑动窗口最大值", "d": "困难", "slug": "sliding-window-maximum", "md": r'''
**题目**：大小为 k 的窗口从左到右滑过数组，返回每个位置的窗口最大值。

**举例**：`nums = [1,3,-1,-3,5,3,6,7], k = 3` → `[3,3,5,5,6,7]`

#### 💡 思路（白话）

- 暴力：每个窗口扫 k 个数找最大，O(nk)，会超时。
- **单调队列**：维护一个「递减」的双端队列，存**下标**。规则只有三条：
  1. 新元素进来前，把队尾所有**比它小**的踢掉（它们在新元素在场时永远当不了最大值，留着没用）；
  2. 新元素下标入队尾；
  3. 队头下标如果滑出了窗口（`<= i - k`），从队头移除。
- 这样队头永远是当前窗口的最大值。
- 直观理解：队列里留下的是「还有希望称王的候选人」，一山更比一山高，前浪比后浪矮就直接出局。

#### ☕ Java

```java
class Solution {
    public int[] maxSlidingWindow(int[] nums, int k) {
        Deque<Integer> dq = new ArrayDeque<>();  // 存下标，对应值递减
        int[] res = new int[nums.length - k + 1];
        for (int i = 0; i < nums.length; i++) {
            while (!dq.isEmpty() && nums[dq.peekLast()] <= nums[i])
                dq.pollLast();                   // 踢掉比我小的
            dq.offerLast(i);
            if (dq.peekFirst() <= i - k)
                dq.pollFirst();                  // 队头已滑出窗口
            if (i >= k - 1)
                res[i - k + 1] = nums[dq.peekFirst()]; // 队头即最大值
        }
        return res;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def maxSlidingWindow(self, nums: List[int], k: int) -> List[int]:
        dq, res = deque(), []
        for i, x in enumerate(nums):
            while dq and nums[dq[-1]] <= x:
                dq.pop()
            dq.append(i)
            if dq[0] <= i - k:
                dq.popleft()
            if i >= k - 1:
                res.append(nums[dq[0]])
        return res
```

#### ⏱ 复杂度

时间 O(n)（每个元素最多进出队一次），空间 O(k)。

**小白提示**：队列里存**下标**而不是值，否则没法判断队头是否滑出窗口。单调队列就这一个模板，本题就是它的代表作。
'''},

{"cat": "substring", "lc": 76, "t": "最小覆盖子串", "d": "困难", "slug": "minimum-window-substring", "md": r'''
**题目**：在字符串 `s` 中找出**最短**的子串，使它包含 `t` 的所有字符（含重复个数）。

**举例**：`s = "ADOBECODEBANC", t = "ABC"` → 返回 `"BANC"`。

#### 💡 思路（白话）

- 滑动窗口求「最短」：`right` 右移直到窗口**合法**（覆盖 t），然后 `left` 尽量右移收缩，每次合法时更新答案。
- 怎么高效判断「覆盖了 t」？维护一个计数器 `needCnt` = 还缺多少个字符：
  - `need[c]` 初始为 t 中各字符的个数；
  - 右端进字符 `c`：若 `need[c] > 0` 说明它是「有用的」，`needCnt--`；然后 `need[c]--`；
  - `needCnt == 0` 即完全覆盖；
  - 左端出字符时反向操作。
- 这样判断合法只要 O(1)，不用每次对比整个计数表。

#### ☕ Java

```java
class Solution {
    public String minWindow(String s, String t) {
        int[] need = new int[128];
        for (char c : t.toCharArray()) need[c]++;
        int needCnt = t.length(), left = 0;
        int bestLen = Integer.MAX_VALUE, bestStart = 0;
        for (int right = 0; right < s.length(); right++) {
            if (need[s.charAt(right)]-- > 0) needCnt--;   // 有用的字符
            while (needCnt == 0) {                        // 已覆盖，收缩
                if (right - left + 1 < bestLen) {
                    bestLen = right - left + 1; bestStart = left;
                }
                if (need[s.charAt(left)]++ == 0) needCnt++; // 移出一个必需字符
                left++;
            }
        }
        return bestLen == Integer.MAX_VALUE ? "" : s.substring(bestStart, bestStart + bestLen);
    }
}
```

#### 🐍 Python

```python
class Solution:
    def minWindow(self, s: str, t: str) -> str:
        need = Counter(t)
        need_cnt, left = len(t), 0
        best = (float('inf'), 0, 0)            # (长度, start, end)
        for right, c in enumerate(s):
            if need[c] > 0:
                need_cnt -= 1
            need[c] -= 1
            while need_cnt == 0:               # 覆盖了，尽量收缩
                if right - left + 1 < best[0]:
                    best = (right - left + 1, left, right)
                lc = s[left]
                need[lc] += 1
                if need[lc] > 0:               # 移走了必需字符
                    need_cnt += 1
                left += 1
        return "" if best[0] == float('inf') else s[best[1]:best[2] + 1]
```

#### ⏱ 复杂度

时间 O(n)，空间 O(128)。

**小白提示**：`need[c]` 允许变成负数——负数表示「这个字符窗口里多了」，这是本题计数技巧的精髓。把「无重复最长子串」练熟再来啃这题。
'''},

{"cat": "array", "lc": 53, "t": "最大子数组和", "d": "中等", "slug": "maximum-subarray", "md": r'''
**题目**：找出一个**连续**子数组，使其和最大，返回这个最大和。

**举例**：`[-2,1,-3,4,-1,2,1,-5,4]` → 最大和子数组是 `[4,-1,2,1]`，返回 6。

#### 💡 思路（白话）

- 动态规划入门第一题。定义 `dp[i]` = **以 nums[i] 结尾**的最大子数组和。
- 走到每个数只有两个选择：
  1. **接上前面**：`dp[i-1] + nums[i]`（前面的积累是正资产）；
  2. **另起炉灶**：就 `nums[i]` 自己（前面的积累是负资产，拖后腿就甩掉）。
- 取大者：`dp[i] = max(dp[i-1] + nums[i], nums[i])`。答案是所有 `dp[i]` 的最大值。
- 因为只依赖前一项，用一个变量滚动即可，空间 O(1)。

#### ☕ Java

```java
class Solution {
    public int maxSubArray(int[] nums) {
        int cur = nums[0], best = nums[0];   // cur = 以当前元素结尾的最大和
        for (int i = 1; i < nums.length; i++) {
            cur = Math.max(cur + nums[i], nums[i]);  // 接上 or 另起炉灶
            best = Math.max(best, cur);
        }
        return best;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def maxSubArray(self, nums: List[int]) -> int:
        cur = best = nums[0]
        for x in nums[1:]:
            cur = max(cur + x, x)
            best = max(best, cur)
        return best
```

#### ⏱ 复杂度

时间 O(n)，空间 O(1)。

**小白提示**：这题学名「Kadane 算法」。记住核心一问：「**前面的累计和是正的吗？是就带上，不是就丢掉**」。它也是后面「乘积最大子数组」的基础。
'''},

{"cat": "array", "lc": 56, "t": "合并区间", "d": "中等", "slug": "merge-intervals", "md": r'''
**题目**：给若干区间，把所有重叠的区间合并。

**举例**：`[[1,3],[2,6],[8,10],[15,18]]` → `[[1,6],[8,10],[15,18]]`（[1,3] 和 [2,6] 重叠合并为 [1,6]）。

#### 💡 思路（白话）

- **区间题第一步：按左端点排序。** 排序后，能合并的区间一定是相邻的。
- 准备一个结果列表，逐个处理区间：
  - 如果当前区间的左端点 ≤ 结果中最后一个区间的右端点 → 有重叠，合并：把最后一个区间的右端点更新为两者较大值；
  - 否则没有重叠，直接追加。

#### ☕ Java

```java
class Solution {
    public int[][] merge(int[][] intervals) {
        Arrays.sort(intervals, (a, b) -> a[0] - b[0]);  // 按左端点排序
        List<int[]> res = new ArrayList<>();
        for (int[] cur : intervals) {
            if (!res.isEmpty() && cur[0] <= res.get(res.size() - 1)[1]) {
                int[] last = res.get(res.size() - 1);   // 重叠 → 合并
                last[1] = Math.max(last[1], cur[1]);
            } else {
                res.add(cur);                           // 不重叠 → 新开一段
            }
        }
        return res.toArray(new int[0][]);
    }
}
```

#### 🐍 Python

```python
class Solution:
    def merge(self, intervals: List[List[int]]) -> List[List[int]]:
        intervals.sort(key=lambda x: x[0])
        res = []
        for cur in intervals:
            if res and cur[0] <= res[-1][1]:
                res[-1][1] = max(res[-1][1], cur[1])
            else:
                res.append(cur)
        return res
```

#### ⏱ 复杂度

时间 O(n log n)（排序），空间 O(n)。

**小白提示**：注意合并时右端点取 `max`——`[1,10]` 和 `[2,3]` 合并后是 `[1,10]` 而不是 `[1,3]`，漏了 max 是最常见的 bug。「先排序再扫一遍」适用于绝大多数区间题。
'''},

{"cat": "array", "lc": 189, "t": "轮转数组", "d": "中等", "slug": "rotate-array", "md": r'''
**题目**：把数组整体向右轮转 k 步，要求原地、O(1) 额外空间。

**举例**：`[1,2,3,4,5,6,7], k = 3` → `[5,6,7,1,2,3,4]`

#### 💡 思路（白话）

- **三次翻转法**（妙招，背下来）：
  1. 整体翻转：`[7,6,5,4,3,2,1]`
  2. 翻转前 k 个：`[5,6,7,4,3,2,1]`
  3. 翻转后 n-k 个：`[5,6,7,1,2,3,4]` ✓
- 为什么对？右移 k 步 = 后 k 个元素搬到前面。整体翻转后，后 k 个就跑到了前面（但顺序反了），再分别把两段翻正即可。
- 注意 `k` 可能大于数组长度，先 `k %= n`。

#### ☕ Java

```java
class Solution {
    public void rotate(int[] nums, int k) {
        int n = nums.length;
        k %= n;
        reverse(nums, 0, n - 1);     // 整体翻转
        reverse(nums, 0, k - 1);     // 翻前 k 个
        reverse(nums, k, n - 1);     // 翻后 n-k 个
    }
    private void reverse(int[] a, int i, int j) {
        while (i < j) {
            int t = a[i]; a[i] = a[j]; a[j] = t;
            i++; j--;
        }
    }
}
```

#### 🐍 Python

```python
class Solution:
    def rotate(self, nums: List[int], k: int) -> None:
        n = len(nums)
        k %= n
        def rev(i, j):
            while i < j:
                nums[i], nums[j] = nums[j], nums[i]
                i += 1; j -= 1
        rev(0, n - 1)
        rev(0, k - 1)
        rev(k, n - 1)
```

#### ⏱ 复杂度

时间 O(n)，空间 O(1)。

**小白提示**：忘了 `k %= n` 会数组越界，这是本题第一坑。如果不要求 O(1) 空间，新建数组 `new[(i+k) % n] = old[i]` 也完全可以，面试先说思路再优化。
'''},

{"cat": "array", "lc": 238, "t": "除自身以外数组的乘积", "d": "中等", "slug": "product-of-array-except-self", "md": r'''
**题目**：返回数组 `answer`，其中 `answer[i]` = 除 `nums[i]` 之外所有元素的乘积。**不能用除法**，O(n) 时间。

**举例**：`[1,2,3,4]` → `[24,12,8,6]`

#### 💡 思路（白话）

- 不能用除法，那就拆开看：`answer[i]` = **i 左边所有数的乘积 × i 右边所有数的乘积**。
- 两遍扫描：
  1. 从左到右，先把 `answer[i]` 填成「i 左边的乘积」（第一个元素左边没东西，记 1）；
  2. 从右到左，用一个变量 `right` 累乘「i 右边的乘积」，乘到 `answer[i]` 上。
- 结果数组不算额外空间，所以是 O(1) 额外空间。

#### ☕ Java

```java
class Solution {
    public int[] productExceptSelf(int[] nums) {
        int n = nums.length;
        int[] answer = new int[n];
        answer[0] = 1;
        for (int i = 1; i < n; i++)
            answer[i] = answer[i - 1] * nums[i - 1];  // 左边的乘积
        int right = 1;                                 // 右边的乘积
        for (int i = n - 1; i >= 0; i--) {
            answer[i] *= right;
            right *= nums[i];
        }
        return answer;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def productExceptSelf(self, nums: List[int]) -> List[int]:
        n = len(nums)
        answer = [1] * n
        for i in range(1, n):
            answer[i] = answer[i - 1] * nums[i - 1]
        right = 1
        for i in range(n - 1, -1, -1):
            answer[i] *= right
            right *= nums[i]
        return answer
```

#### ⏱ 复杂度

时间 O(n)，空间 O(1)（不算结果数组）。

**小白提示**：「前缀 × 后缀」是一种通用思想：当某个位置的答案 = 左边的信息 + 右边的信息时，就左右各扫一遍。面试追问「为什么不能用除法」：因为数组可能有 0。
'''},

{"cat": "array", "lc": 41, "t": "缺失的第一个正数", "d": "困难", "slug": "first-missing-positive", "md": r'''
**题目**：找出数组中**缺失的最小正整数**。要求 O(n) 时间、O(1) 空间。

**举例**：`[3,4,-1,1]` → 返回 2；`[1,2,0]` → 返回 3。

#### 💡 思路（白话）

- 关键观察：长度为 n 的数组，答案一定在 `1 ~ n+1` 之间（最好情况 1..n 都在，答案 n+1）。
- 不能开新空间，就**把数组自己当哈希表**（原地哈希）：让数值 `x` 回到下标 `x-1` 的位置上（1 放在位置 0，2 放在位置 1……）。
- 一遍扫描：只要 `nums[i]` 在 `1..n` 范围内、且它该去的位置上放的不是它，就把它交换过去。注意是 **while 不是 if**——换过来的新数可能还要继续换。
- 归位完成后再扫一遍：第一个 `nums[i] != i+1` 的位置，答案就是 `i+1`。

#### ☕ Java

```java
class Solution {
    public int firstMissingPositive(int[] nums) {
        int n = nums.length;
        for (int i = 0; i < n; i++) {
            // 把 nums[i] 送回它该在的位置 nums[i]-1，直到送不动
            while (nums[i] >= 1 && nums[i] <= n && nums[nums[i] - 1] != nums[i]) {
                int t = nums[nums[i] - 1];
                nums[nums[i] - 1] = nums[i];
                nums[i] = t;
            }
        }
        for (int i = 0; i < n; i++)
            if (nums[i] != i + 1) return i + 1;
        return n + 1;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def firstMissingPositive(self, nums: List[int]) -> int:
        n = len(nums)
        for i in range(n):
            while 1 <= nums[i] <= n and nums[nums[i] - 1] != nums[i]:
                # 把 nums[i] 换到下标 nums[i]-1 处
                j = nums[i] - 1
                nums[i], nums[j] = nums[j], nums[i]
        for i in range(n):
            if nums[i] != i + 1:
                return i + 1
        return n + 1
```

#### ⏱ 复杂度

时间 O(n)（每个数最多被交换一次到位），空间 O(1)。

**小白提示**：交换条件写 `nums[nums[i]-1] != nums[i]` 而不是 `nums[i] != i+1`，否则遇到重复数会死循环——这是本题最隐蔽的坑。「原地哈希：值 x 放到下标 x-1」这个思想还会在「寻找重复数」等题出现。
'''},

{"cat": "matrix", "lc": 73, "t": "矩阵置零", "d": "中等", "slug": "set-matrix-zeroes", "md": r'''
**题目**：矩阵中若某元素为 0，把它所在的**整行和整列**都置 0。要求原地操作。

**举例**：`[[1,1,1],[1,0,1],[1,1,1]]` → `[[1,0,1],[0,0,0],[1,0,1]]`

#### 💡 思路（白话）

- 不能边扫边置零（会把后面的 1 误判）。需要先**记下**哪些行、哪些列要清零，再统一动手。
- 简单做法：两个标记数组 `rowZero[m]`、`colZero[n]`，空间 O(m+n)，完全够用。
- 进阶 O(1) 空间：**用矩阵的第一行和第一列当标记本**——`matrix[i][0] = 0` 表示第 i 行要清零，`matrix[0][j] = 0` 表示第 j 列要清零。但第一行/列自己也可能要清零，先用两个布尔变量单独记下来，最后处理。

#### ☕ Java

```java
class Solution {
    public void setZeroes(int[][] matrix) {
        int m = matrix.length, n = matrix[0].length;
        boolean row0 = false, col0 = false;
        for (int j = 0; j < n; j++) if (matrix[0][j] == 0) row0 = true;
        for (int i = 0; i < m; i++) if (matrix[i][0] == 0) col0 = true;
        for (int i = 1; i < m; i++)
            for (int j = 1; j < n; j++)
                if (matrix[i][j] == 0) { matrix[i][0] = 0; matrix[0][j] = 0; }
        for (int i = 1; i < m; i++)
            for (int j = 1; j < n; j++)
                if (matrix[i][0] == 0 || matrix[0][j] == 0) matrix[i][j] = 0;
        if (row0) for (int j = 0; j < n; j++) matrix[0][j] = 0;
        if (col0) for (int i = 0; i < m; i++) matrix[i][0] = 0;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def setZeroes(self, matrix: List[List[int]]) -> None:
        m, n = len(matrix), len(matrix[0])
        rows, cols = set(), set()          # O(m+n) 标记法，简单清晰
        for i in range(m):
            for j in range(n):
                if matrix[i][j] == 0:
                    rows.add(i); cols.add(j)
        for i in range(m):
            for j in range(n):
                if i in rows or j in cols:
                    matrix[i][j] = 0
```

#### ⏱ 复杂度

时间 O(mn)；空间：标记法 O(m+n)，首行首列法 O(1)。

**小白提示**：面试先写 O(m+n) 标记法（5 分钟写完不出错），再口述 O(1) 优化思路，比直接硬写 O(1) 版本翻车强得多。
'''},

{"cat": "matrix", "lc": 54, "t": "螺旋矩阵", "d": "中等", "slug": "spiral-matrix", "md": r'''
**题目**：按顺时针螺旋顺序返回矩阵的所有元素。

**举例**：`[[1,2,3],[4,5,6],[7,8,9]]` → `[1,2,3,6,9,8,7,4,5]`

#### 💡 思路（白话）

- 维护四个边界：`top`、`bottom`、`left`、`right`，像剥洋葱一圈圈往里走：
  1. 沿 top 行从左到右 → `top++`（这行用完了）
  2. 沿 right 列从上到下 → `right--`
  3. 沿 bottom 行从右到左 → `bottom--`
  4. 沿 left 列从下到上 → `left++`
- 每走完一条边**立刻检查边界是否交错**（`top > bottom` 或 `left > right`），交错就结束——否则单行/单列的「尾巴」会被重复走。

#### ☕ Java

```java
class Solution {
    public List<Integer> spiralOrder(int[][] matrix) {
        List<Integer> res = new ArrayList<>();
        int top = 0, bottom = matrix.length - 1;
        int left = 0, right = matrix[0].length - 1;
        while (top <= bottom && left <= right) {
            for (int j = left; j <= right; j++) res.add(matrix[top][j]);
            top++;
            for (int i = top; i <= bottom; i++) res.add(matrix[i][right]);
            right--;
            if (top > bottom || left > right) break;   // 防止回头重复走
            for (int j = right; j >= left; j--) res.add(matrix[bottom][j]);
            bottom--;
            for (int i = bottom; i >= top; i--) res.add(matrix[i][left]);
            left++;
        }
        return res;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def spiralOrder(self, matrix: List[List[int]]) -> List[int]:
        res = []
        top, bottom = 0, len(matrix) - 1
        left, right = 0, len(matrix[0]) - 1
        while top <= bottom and left <= right:
            for j in range(left, right + 1): res.append(matrix[top][j])
            top += 1
            for i in range(top, bottom + 1): res.append(matrix[i][right])
            right -= 1
            if top > bottom or left > right: break
            for j in range(right, left - 1, -1): res.append(matrix[bottom][j])
            bottom -= 1
            for i in range(bottom, top - 1, -1): res.append(matrix[i][left])
            left += 1
        return res
```

#### ⏱ 复杂度

时间 O(mn)，空间 O(1)（不算结果）。

**小白提示**：拿一个 3×4 和一个 1×4 的矩阵在纸上各走一遍，体会中间那个 `break` 为什么不能少（单行矩阵走完第 1、2 步后必须停）。
'''},

{"cat": "matrix", "lc": 48, "t": "旋转图像", "d": "中等", "slug": "rotate-image", "md": r'''
**题目**：把 n×n 矩阵**原地**顺时针旋转 90°。

**举例**：`[[1,2,3],[4,5,6],[7,8,9]]` → `[[7,4,1],[8,5,2],[9,6,3]]`

#### 💡 思路（白话）

- 神级分解：**顺时针转 90° = 先转置（沿主对角线翻折）+ 再水平翻转（每行左右对调）**。
  - 转置：`[[1,2,3],[4,5,6],[7,8,9]]` → `[[1,4,7],[2,5,8],[3,6,9]]`
  - 每行翻转：→ `[[7,4,1],[8,5,2],[9,6,3]]` ✓
- 两步都是简单的交换操作，不会出下标错。
- 顺带记：逆时针 90° = 转置 + **上下**翻转。

#### ☕ Java

```java
class Solution {
    public void rotate(int[][] matrix) {
        int n = matrix.length;
        for (int i = 0; i < n; i++)            // 1. 转置（只遍历上三角）
            for (int j = i + 1; j < n; j++) {
                int t = matrix[i][j];
                matrix[i][j] = matrix[j][i];
                matrix[j][i] = t;
            }
        for (int[] row : matrix) {             // 2. 每行左右翻转
            for (int l = 0, r = n - 1; l < r; l++, r--) {
                int t = row[l]; row[l] = row[r]; row[r] = t;
            }
        }
    }
}
```

#### 🐍 Python

```python
class Solution:
    def rotate(self, matrix: List[List[int]]) -> None:
        n = len(matrix)
        for i in range(n):                 # 转置
            for j in range(i + 1, n):
                matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
        for row in matrix:                 # 每行翻转
            row.reverse()
```

#### ⏱ 复杂度

时间 O(n²)，空间 O(1)。

**小白提示**：转置时内层循环从 `j = i+1` 开始（只扫上三角），从 0 开始会把每对元素换两次、等于没换——初学 100% 踩这个坑。
'''},

{"cat": "matrix", "lc": 240, "t": "搜索二维矩阵 II", "d": "中等", "slug": "search-a-2d-matrix-ii", "md": r'''
**题目**：矩阵每行从左到右递增、每列从上到下递增，判断 target 是否存在。

**举例**：在 `[[1,4,7],[2,5,8],[3,6,9]]` 中找 5 → true。

#### 💡 思路（白话）

- 站在**右上角**看这个矩阵，它就像一棵二叉搜索树：往左走变小，往下走变大。
- 从右上角出发：
  - 当前值 == target → 找到；
  - 当前值 > target → 这一**列**下面只会更大，全部排除，**左移**；
  - 当前值 < target → 这一**行**左边只会更小，全部排除，**下移**。
- 每步排除一行或一列，最多走 m+n 步。

#### ☕ Java

```java
class Solution {
    public boolean searchMatrix(int[][] matrix, int target) {
        int i = 0, j = matrix[0].length - 1;   // 从右上角出发
        while (i < matrix.length && j >= 0) {
            if (matrix[i][j] == target) return true;
            else if (matrix[i][j] > target) j--;  // 排除这一列
            else i++;                              // 排除这一行
        }
        return false;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def searchMatrix(self, matrix: List[List[int]], target: int) -> bool:
        i, j = 0, len(matrix[0]) - 1
        while i < len(matrix) and j >= 0:
            if matrix[i][j] == target:
                return True
            elif matrix[i][j] > target:
                j -= 1
            else:
                i += 1
        return False
```

#### ⏱ 复杂度

时间 O(m + n)，空间 O(1)。

**小白提示**：起点只能是**右上角或左下角**（一个方向变大、另一个变小才能做决策）；从左上角出发两个方向都变大，没法判断往哪走。这题被称为「楼梯走法」，代码 10 行，性价比极高。
'''},
]
