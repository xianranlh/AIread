# LeetCode Hot 100 讲义 · Part 6：栈(5) + 堆(3) + 贪心(4)
PROBLEMS = [
{"cat": "stack", "lc": 20, "t": "有效的括号", "d": "简单", "slug": "valid-parentheses", "md": r'''
**题目**：判断由 `()[]{}` 组成的字符串括号是否有效（正确闭合、顺序正确）。

#### 💡 思路（白话）

- 最后打开的括号必须最先闭合——「后开先关」正是栈的「后进先出」。
- 遍历字符串：左括号入栈；右括号则检查栈顶是不是配对的左括号，是就弹出，不是（或栈空）就无效。
- 扫完后栈必须为空（所有左括号都被关上了）。

#### ☕ Java

```java
class Solution {
    public boolean isValid(String s) {
        Deque<Character> stack = new ArrayDeque<>();
        for (char c : s.toCharArray()) {
            if (c == '(') stack.push(')');        // 妙招：入栈时直接存「期望的右括号」
            else if (c == '[') stack.push(']');
            else if (c == '{') stack.push('}');
            else if (stack.isEmpty() || stack.pop() != c) return false;
        }
        return stack.isEmpty();
    }
}
```

#### 🐍 Python

```python
class Solution:
    def isValid(self, s: str) -> bool:
        pairs = {')': '(', ']': '[', '}': '{'}
        stack = []
        for c in s:
            if c in pairs:                       # 右括号：栈顶必须配对
                if not stack or stack.pop() != pairs[c]:
                    return False
            else:
                stack.append(c)                  # 左括号入栈
        return not stack
```

#### ⏱ 复杂度

时间 O(n)，空间 O(n)。

**小白提示**：两个易漏的边界：右括号来了但**栈是空的**（`"]"`）、扫完了**栈不空**（`"("`）。Java 版「入栈存期望右括号」的写法把比较简化成一个 `!=`，很优雅。
'''},

{"cat": "stack", "lc": 155, "t": "最小栈", "d": "中等", "slug": "min-stack", "md": r'''
**题目**：设计一个栈，除 push/pop/top 外，还要能 **O(1)** 返回栈中最小元素。

#### 💡 思路（白话）

- 难点：弹出最小值后，「第二小」是谁？普通变量记不住历史。
- **辅助栈**：再开一个栈 `minStack`，与主栈同步进出，但它存的是「**到目前为止的最小值**」——每次 push 时压入 `min(新元素, 当前最小)`。
- 这样任何时刻 `minStack` 的栈顶都是主栈当前所有元素的最小值，弹出时两个栈一起弹，历史最小值自动恢复。

#### ☕ Java

```java
class MinStack {
    private final Deque<Integer> stack = new ArrayDeque<>();
    private final Deque<Integer> minStack = new ArrayDeque<>();

    public MinStack() {}

    public void push(int val) {
        stack.push(val);
        minStack.push(minStack.isEmpty() ? val : Math.min(val, minStack.peek()));
    }
    public void pop() {
        stack.pop();
        minStack.pop();      // 同步弹出
    }
    public int top() { return stack.peek(); }
    public int getMin() { return minStack.peek(); }
}
```

#### 🐍 Python

```python
class MinStack:
    def __init__(self):
        self.stack = []
        self.min_stack = []

    def push(self, val: int) -> None:
        self.stack.append(val)
        self.min_stack.append(val if not self.min_stack else min(val, self.min_stack[-1]))

    def pop(self) -> None:
        self.stack.pop()
        self.min_stack.pop()

    def top(self) -> int:
        return self.stack[-1]

    def getMin(self) -> int:
        return self.min_stack[-1]
```

#### ⏱ 复杂度

所有操作 O(1)，空间 O(n)。

**小白提示**：「**用空间换时间 + 同步维护辅助结构**」是数据结构设计题的通用思想。面试常见追问「能否少存点？」：辅助栈只在新值 ≤ 当前最小时才压入（弹出时判断相等才弹），可以省一些空间。
'''},

{"cat": "stack", "lc": 394, "t": "字符串解码", "d": "中等", "slug": "decode-string", "md": r'''
**题目**：解码 `k[str]` 格式：`3[a]` → `aaa`，`3[a2[c]]` → `accaccacc`（可嵌套）。

#### 💡 思路（白话）

- 嵌套结构 → 栈。遇到 `[` 说明要进入新一层，**把当前攒的字符串和数字存档（入栈）**，清空重来；遇到 `]` 说明这层结束，**取出存档**：`结果 = 存档字符串 + 存档数字 × 本层字符串`。
- 维护两个变量：`curStr`（本层攒的字符串）、`curNum`（正在读的数字，注意多位数 `12[a]`）。
- 数字栈和字符串栈配对使用（或合并成一个栈存二元组）。

#### ☕ Java

```java
class Solution {
    public String decodeString(String s) {
        Deque<Integer> numStack = new ArrayDeque<>();
        Deque<StringBuilder> strStack = new ArrayDeque<>();
        StringBuilder cur = new StringBuilder();
        int num = 0;
        for (char c : s.toCharArray()) {
            if (Character.isDigit(c)) {
                num = num * 10 + (c - '0');          // 多位数
            } else if (c == '[') {
                numStack.push(num); strStack.push(cur);   // 存档
                num = 0; cur = new StringBuilder();
            } else if (c == ']') {
                StringBuilder outer = strStack.pop();      // 取档
                int k = numStack.pop();
                for (int i = 0; i < k; i++) outer.append(cur);
                cur = outer;
            } else {
                cur.append(c);
            }
        }
        return cur.toString();
    }
}
```

#### 🐍 Python

```python
class Solution:
    def decodeString(self, s: str) -> str:
        stack = []                  # 存 (外层字符串, 重复次数)
        cur, num = "", 0
        for c in s:
            if c.isdigit():
                num = num * 10 + int(c)
            elif c == '[':
                stack.append((cur, num))
                cur, num = "", 0
            elif c == ']':
                outer, k = stack.pop()
                cur = outer + cur * k
            else:
                cur += c
        return cur
```

#### ⏱ 复杂度

时间 O(解码后长度)，空间 O(嵌套深度 × 字符串长)。

**小白提示**：拿 `3[a2[c]]` 在纸上模拟一遍栈的进出，立刻就懂。两个坑：数字可能是多位数（`num*10+digit` 累加）；`]` 时是「外层 + 内层×k」，顺序别接反。
'''},

{"cat": "stack", "lc": 739, "t": "每日温度", "d": "中等", "slug": "daily-temperatures", "md": r'''
**题目**：给每日温度数组，对每一天求「还要等几天才有更高的温度」，没有则为 0。

**举例**：`[73,74,75,71,69,72,76,73]` → `[1,1,4,2,1,1,0,0]`

#### 💡 思路（白话）

- 「下一个比我大的元素在哪」→ **单调栈**经典题。
- 栈里存**下标**，对应温度从栈底到栈顶**递减**（都是「还没等到更暖天」的日子）。
- 新温度来了：比栈顶的温度高 → 栈顶那天「等到了」！弹出并计算等待天数（下标差），继续比较新栈顶……然后自己入栈等待。
- 每个元素最多进出栈一次，O(n)。

#### ☕ Java

```java
class Solution {
    public int[] dailyTemperatures(int[] temperatures) {
        int n = temperatures.length;
        int[] res = new int[n];
        Deque<Integer> stack = new ArrayDeque<>();   // 存下标，温度递减
        for (int i = 0; i < n; i++) {
            while (!stack.isEmpty() && temperatures[i] > temperatures[stack.peek()]) {
                int j = stack.pop();          // 第 j 天等到了更暖的第 i 天
                res[j] = i - j;
            }
            stack.push(i);
        }
        return res;       // 留在栈里的没等到，res 默认 0
    }
}
```

#### 🐍 Python

```python
class Solution:
    def dailyTemperatures(self, temperatures: List[int]) -> List[int]:
        n = len(temperatures)
        res = [0] * n
        stack = []
        for i, t in enumerate(temperatures):
            while stack and t > temperatures[stack[-1]]:
                j = stack.pop()
                res[j] = i - j
            stack.append(i)
        return res
```

#### ⏱ 复杂度

时间 O(n)，空间 O(n)。

**小白提示**：单调栈的判断口诀：「**找下一个更大 → 维护递减栈；找下一个更小 → 维护递增栈**」。这是单调栈的入门题，写熟它再去挑战「柱状图中最大的矩形」。
'''},

{"cat": "stack", "lc": 84, "t": "柱状图中最大的矩形", "d": "困难", "slug": "largest-rectangle-in-histogram", "md": r'''
**题目**：柱状图中能勾勒出的最大矩形面积。`[2,1,5,6,2,3]` → 10（高 5、6 的两根柱子撑起 5×2）。

#### 💡 思路（白话）

- 换个角度想：**以每根柱子的高度为矩形的高**，它能向左右延伸多远？延伸到两边第一根**比它矮**的柱子为止。面积 = 高 × (右边界 - 左边界 - 1)。
- 「左右第一个更小的元素」→ 单调**递增**栈：
  - 新柱子比栈顶矮 → 栈顶柱子的「右边界」找到了（就是新柱子），弹出结算：它的左边界是弹出后的新栈顶。
- 首尾各加一根高度 0 的「哨兵」柱：尾哨兵保证所有柱子最后都被结算，头哨兵免去栈空判断。

#### ☕ Java

```java
class Solution {
    public int largestRectangleArea(int[] heights) {
        int n = heights.length;
        int[] h = new int[n + 2];                  // 首尾加哨兵 0
        System.arraycopy(heights, 0, h, 1, n);
        Deque<Integer> stack = new ArrayDeque<>();
        int best = 0;
        for (int i = 0; i < h.length; i++) {
            while (!stack.isEmpty() && h[i] < h[stack.peek()]) {
                int height = h[stack.pop()];       // 被结算的柱子
                int width = i - stack.peek() - 1;  // 右边界 i，左边界新栈顶
                best = Math.max(best, height * width);
            }
            stack.push(i);
        }
        return best;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def largestRectangleArea(self, heights: List[int]) -> int:
        h = [0] + heights + [0]          # 哨兵
        stack, best = [0], 0
        for i in range(1, len(h)):
            while stack and h[i] < h[stack[-1]]:
                height = h[stack.pop()]
                width = i - stack[-1] - 1
                best = max(best, height * width)
            stack.append(i)
        return best
```

#### ⏱ 复杂度

时间 O(n)，空间 O(n)。

**小白提示**：理解的关键一句：「**柱子出栈的时刻，它的左右边界同时确定**」（右边界=逼它出栈的柱子，左边界=它身下的栈顶）。哨兵技巧让代码少一半边界判断，强烈推荐。
'''},

{"cat": "heap", "lc": 215, "t": "数组中的第K个最大元素", "d": "中等", "slug": "kth-largest-element-in-an-array", "md": r'''
**题目**：找数组中第 k 大的元素（不是去重后的第 k 个），要求 O(n)。

#### 💡 思路（白话）

- **小顶堆法**（最实用）：维护一个**大小为 k 的小顶堆**，扫描数组：堆没满就进；堆满了且新数比堆顶大，就替换堆顶。扫完后堆顶就是第 k 大。O(n log k)。
  - 为什么是小顶堆？堆里存的是「当前最大的 k 个数」，堆顶是其中**最小**的，正好是第 k 大、也是「守门员」。
- 严格 O(n) 的快速选择（快排的分区思想，每次只递归一边）面试可口述。

#### ☕ Java

```java
class Solution {
    public int findKthLargest(int[] nums, int k) {
        PriorityQueue<Integer> heap = new PriorityQueue<>();  // 小顶堆
        for (int x : nums) {
            if (heap.size() < k) heap.offer(x);
            else if (x > heap.peek()) {     // 比守门员大，挤掉它
                heap.poll();
                heap.offer(x);
            }
        }
        return heap.peek();
    }
}
```

#### 🐍 Python

```python
class Solution:
    def findKthLargest(self, nums: List[int], k: int) -> int:
        heap = []
        for x in nums:
            if len(heap) < k:
                heapq.heappush(heap, x)
            elif x > heap[0]:
                heapq.heapreplace(heap, x)   # 弹堆顶 + 压新值，一步到位
        return heap[0]
```

#### ⏱ 复杂度

时间 O(n log k)，空间 O(k)。

**小白提示**：「第 k **大**用**小**顶堆，第 k **小**用**大**顶堆」——口诀反着记。这个模板是海量数据面试题的标准答案（10 亿个数取前 100：堆只占 100 个位置，数据流式处理）。
'''},

{"cat": "heap", "lc": 347, "t": "前 K 个高频元素", "d": "中等", "slug": "top-k-frequent-elements", "md": r'''
**题目**：返回数组中出现频率最高的前 k 个元素。

#### 💡 思路（白话）

- 两步走：
  1. 哈希表统计每个数的出现次数；
  2. 「按次数取前 k 个」= Top K 问题 → 大小为 k 的**小顶堆**（按次数比较）：堆满后，新元素次数比堆顶大就替换。
- O(n log k)，比「全部排序取前 k」的 O(n log n) 好，k 小的时候优势明显。

#### ☕ Java

```java
class Solution {
    public int[] topKFrequent(int[] nums, int k) {
        Map<Integer, Integer> count = new HashMap<>();
        for (int x : nums) count.merge(x, 1, Integer::sum);
        PriorityQueue<int[]> heap =                        // [数值, 次数] 按次数小顶堆
            new PriorityQueue<>((a, b) -> a[1] - b[1]);
        for (Map.Entry<Integer, Integer> e : count.entrySet()) {
            if (heap.size() < k) heap.offer(new int[]{e.getKey(), e.getValue()});
            else if (e.getValue() > heap.peek()[1]) {
                heap.poll();
                heap.offer(new int[]{e.getKey(), e.getValue()});
            }
        }
        int[] res = new int[k];
        for (int i = 0; i < k; i++) res[i] = heap.poll()[0];
        return res;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def topKFrequent(self, nums: List[int], k: int) -> List[int]:
        count = Counter(nums)
        # heapq.nlargest 内部就是维护 k 大小的堆
        return [x for x, _ in count.most_common(k)]
```

#### ⏱ 复杂度

时间 O(n log k)，空间 O(n)。

**小白提示**：Python 的 `Counter.most_common(k)` 一行出答案，但面试要会讲背后的堆原理。进阶谈资：桶排序法（下标=出现次数的桶）可以做到严格 O(n)。
'''},

{"cat": "heap", "lc": 295, "t": "数据流的中位数", "d": "困难", "slug": "find-median-from-data-stream", "md": r'''
**题目**：设计数据结构，支持不断添加数字 `addNum`，并随时返回当前所有数字的中位数 `findMedian`。

#### 💡 思路（白话）

- **对顶堆**：把所有数分成两半——
  - `maxHeap`（大顶堆）：存**较小的一半**，堆顶是这半边的最大值；
  - `minHeap`（小顶堆）：存**较大的一半**，堆顶是这半边的最小值。
- 保持两个约束：① maxHeap 的所有数 ≤ minHeap 的所有数；② 两堆大小差 ≤ 1（约定 maxHeap 可多 1 个）。
- 添加数字的无脑安全写法：**先压进 maxHeap，弹出 maxHeap 堆顶压进 minHeap**（保证约束①）；若 minHeap 比 maxHeap 大，再倒回去一个（保证约束②）。
- 中位数：总数奇数 → maxHeap 堆顶；偶数 → 两堆顶平均。

#### ☕ Java

```java
class MedianFinder {
    private final PriorityQueue<Integer> maxHeap =      // 较小的一半
        new PriorityQueue<>(Collections.reverseOrder());
    private final PriorityQueue<Integer> minHeap =      // 较大的一半
        new PriorityQueue<>();

    public MedianFinder() {}

    public void addNum(int num) {
        maxHeap.offer(num);
        minHeap.offer(maxHeap.poll());        // 平衡值域
        if (minHeap.size() > maxHeap.size())
            maxHeap.offer(minHeap.poll());    // 平衡大小
    }
    public double findMedian() {
        if (maxHeap.size() > minHeap.size()) return maxHeap.peek();
        return (maxHeap.peek() + minHeap.peek()) / 2.0;
    }
}
```

#### 🐍 Python

```python
class MedianFinder:
    def __init__(self):
        self.small = []   # 大顶堆（取负实现），较小的一半
        self.large = []   # 小顶堆，较大的一半

    def addNum(self, num: int) -> None:
        heapq.heappush(self.small, -num)
        heapq.heappush(self.large, -heapq.heappop(self.small))
        if len(self.large) > len(self.small):
            heapq.heappush(self.small, -heapq.heappop(self.large))

    def findMedian(self) -> float:
        if len(self.small) > len(self.large):
            return -self.small[0]
        return (-self.small[0] + self.large[0]) / 2
```

#### ⏱ 复杂度

addNum O(log n)，findMedian O(1)，空间 O(n)。

**小白提示**：「先压 A、A 顶倒给 B、B 太大倒回 A」这套三步操作不管来什么数都能保持两个约束，背下来不用临场推。Python 没有大顶堆，**取负数存**是标准技巧。
'''},

{"cat": "greedy", "lc": 121, "t": "买卖股票的最佳时机", "d": "简单", "slug": "best-time-to-buy-and-sell-stock", "md": r'''
**题目**：数组是每天的股价，只能买卖**一次**（先买后卖），求最大利润；无利润返回 0。

**举例**：`[7,1,5,3,6,4]` → 第 2 天 1 元买、第 5 天 6 元卖，利润 5。

#### 💡 思路（白话）

- 在第 i 天卖出的最大利润 = `第 i 天价格 - 前 i-1 天的最低价`。
- 所以一遍扫描，同时维护两个量：
  - `minPrice`：到目前为止的历史最低价（最佳买入点）；
  - `best`：今天卖能赚多少，更新最大利润。
- 贪心点：**买入永远选历史最低**，不用犹豫。

#### ☕ Java

```java
class Solution {
    public int maxProfit(int[] prices) {
        int minPrice = Integer.MAX_VALUE, best = 0;
        for (int p : prices) {
            minPrice = Math.min(minPrice, p);       // 历史最低价
            best = Math.max(best, p - minPrice);    // 今天卖的利润
        }
        return best;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        min_price, best = float('inf'), 0
        for p in prices:
            min_price = min(min_price, p)
            best = max(best, p - min_price)
        return best
```

#### ⏱ 复杂度

时间 O(n)，空间 O(1)。

**小白提示**：注意必须「先买后卖」，所以是「先更新最低价再算利润」（或者反过来先算利润再更新也对，想想为什么都行）。两层暴力循环也能过脑子，但这个 O(n) 写法是面试标准答案。
'''},

{"cat": "greedy", "lc": 55, "t": "跳跃游戏", "d": "中等", "slug": "jump-game", "md": r'''
**题目**：数组 `nums[i]` 表示在位置 i 最多能往前跳几步，从位置 0 出发，能否到达最后一个位置？

**举例**：`[2,3,1,1,4]` → true；`[3,2,1,0,4]` → false（必然停在下标 3）。

#### 💡 思路（白话）

- 不用纠结具体怎么跳，只维护一个量：**`farthest` = 目前能到达的最远位置**。
- 从左到右遍历每个位置 i：
  - 如果 `i > farthest` → 连 i 都到不了，直接 false；
  - 否则更新 `farthest = max(farthest, i + nums[i])`；
  - `farthest` 够到最后一格 → true。
- 贪心点：能到达的范围是连续的，只要最远点过线就赢。

#### ☕ Java

```java
class Solution {
    public boolean canJump(int[] nums) {
        int farthest = 0;
        for (int i = 0; i < nums.length; i++) {
            if (i > farthest) return false;          // 这格都到不了
            farthest = Math.max(farthest, i + nums[i]);
            if (farthest >= nums.length - 1) return true;
        }
        return true;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def canJump(self, nums: List[int]) -> bool:
        farthest = 0
        for i, x in enumerate(nums):
            if i > farthest:
                return False
            farthest = max(farthest, i + x)
        return True
```

#### ⏱ 复杂度

时间 O(n)，空间 O(1)。

**小白提示**：把「跳跃」翻译成「可达范围」是本题的顿悟点——`[0, farthest]` 内的每一格都可达。`if i > farthest` 的判断要放在更新之前，顺序错了会误判。
'''},

{"cat": "greedy", "lc": 45, "t": "跳跃游戏 II", "d": "中等", "slug": "jump-game-ii", "md": r'''
**题目**：和上题一样的跳跃规则（保证一定能到终点），求跳到最后一格的**最少跳跃次数**。

**举例**：`[2,3,1,1,4]` → 2（0→1→4）。

#### 💡 思路（白话）

- 把每一跳看成一个「层」（BFS 思想）：第一跳覆盖 `[1, nums[0]]`，第二跳覆盖这些点能到的最远范围……
- 三个变量：`end`（当前这一跳的边界）、`farthest`（下一跳能到的最远点）、`jumps`。
- 遍历到 i：更新 `farthest`；当 `i == end`（这一跳的范围走完了），必须起跳：`jumps++`，`end = farthest`。
- 贪心点：在当前跳的范围内，**下一跳一定选「能到最远」的落点**。

#### ☕ Java

```java
class Solution {
    public int jump(int[] nums) {
        int jumps = 0, end = 0, farthest = 0;
        for (int i = 0; i < nums.length - 1; i++) {  // 注意：不含最后一格
            farthest = Math.max(farthest, i + nums[i]);
            if (i == end) {        // 当前跳的范围用完，必须再跳一次
                jumps++;
                end = farthest;
            }
        }
        return jumps;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def jump(self, nums: List[int]) -> int:
        jumps = end = farthest = 0
        for i in range(len(nums) - 1):
            farthest = max(farthest, i + nums[i])
            if i == end:
                jumps += 1
                end = farthest
        return jumps
```

#### ⏱ 复杂度

时间 O(n)，空间 O(1)。

**小白提示**：循环写 `len - 1`（不遍历最后一格）是关键——站上终点就不用再跳了，遍历到终点会多算一次。把它理解成「BFS 分层，层数即答案」就再也不会忘。
'''},

{"cat": "greedy", "lc": 763, "t": "划分字母区间", "d": "中等", "slug": "partition-labels", "md": r'''
**题目**：把字符串划分成尽量多的片段，要求**同一字母只能出现在一个片段里**，返回每段长度。

**举例**：`"ababcbacadefegde..."` → 第一段必须包含所有 a/b/c，到它们最后一次出现处结束。

#### 💡 思路（白话）

- 先扫一遍，记下**每个字母最后一次出现的位置** `last[c]`。
- 再扫一遍划分：维护当前片段的右边界 `end = max(end, last[当前字母])`——片段里出现过的每个字母都「拖着」边界到它的最后出现位置。
- 当 `i == end`：边界没有被继续拖远，当前片段可以收尾，记录长度，开始下一段。
- 和「跳跃游戏 II」神似：都是「遍历中不断扩张右边界，到达边界时结算」。

#### ☕ Java

```java
class Solution {
    public List<Integer> partitionLabels(String s) {
        int[] last = new int[26];
        for (int i = 0; i < s.length(); i++)
            last[s.charAt(i) - 'a'] = i;             // 每个字母最后出现的位置
        List<Integer> res = new ArrayList<>();
        int start = 0, end = 0;
        for (int i = 0; i < s.length(); i++) {
            end = Math.max(end, last[s.charAt(i) - 'a']);  // 拖动边界
            if (i == end) {                          // 到达边界，收尾
                res.add(end - start + 1);
                start = i + 1;
            }
        }
        return res;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def partitionLabels(self, s: str) -> List[int]:
        last = {c: i for i, c in enumerate(s)}   # 后出现的自动覆盖
        res, start, end = [], 0, 0
        for i, c in enumerate(s):
            end = max(end, last[c])
            if i == end:
                res.append(end - start + 1)
                start = i + 1
        return res
```

#### ⏱ 复杂度

时间 O(n)，空间 O(26)。

**小白提示**：Python 版用字典推导式建 `last` 很巧：遍历时后面的下标自动覆盖前面的，一行得到「最后出现位置」。「预处理 + 一遍扫描」是字符串贪心题的常见节奏。
'''},
]
