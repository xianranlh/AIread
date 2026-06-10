# LeetCode Hot 100 讲义 · Part 1：哈希(3) + 双指针(4) + 滑动窗口(2)
PROBLEMS = [
{"cat": "hash", "lc": 1, "t": "两数之和", "d": "简单", "slug": "two-sum", "md": r'''
**题目**：给一个整数数组 `nums` 和目标值 `target`，找出**和为 target 的两个数**的下标。每种输入只对应一个答案。

**举例**：`nums = [2,7,11,15], target = 9` → 因为 `2 + 7 = 9`，返回 `[0,1]`。

#### 💡 思路（白话）

- 最笨的办法：两层循环，把每一对都试一遍，O(n²)。
- 换个角度：遍历到数字 `x` 时，我其实在找「`target - x` 这个数之前出现过没有？」——**「出现过没有」就是哈希表最擅长的事**。
- 做法：准备一个 map，存「数值 → 下标」。每遍历到一个数，先查 `target - x` 在不在 map 里：在，直接返回两个下标；不在，把自己存进 map，继续。
- 一遍扫完就能出结果，每个数只看一次。

#### ☕ Java

```java
class Solution {
    public int[] twoSum(int[] nums, int target) {
        Map<Integer, Integer> map = new HashMap<>(); // 数值 -> 下标
        for (int i = 0; i < nums.length; i++) {
            int need = target - nums[i];      // 我需要找的「另一半」
            if (map.containsKey(need)) {
                return new int[]{map.get(need), i};
            }
            map.put(nums[i], i);              // 没找到，把自己登记进去
        }
        return new int[0]; // 题目保证有解，走不到这里
    }
}
```

#### 🐍 Python

```python
class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        seen = {}                      # 数值 -> 下标
        for i, x in enumerate(nums):
            if target - x in seen:     # 另一半出现过？
                return [seen[target - x], i]
            seen[x] = i
```

#### ⏱ 复杂度

时间 O(n)，空间 O(n)。

**小白提示**：这是力扣第 1 题、面试出现率最高的题。记住口诀：「**边遍历边查表，查的是 target 减自己**」。注意要先查再存，避免 `target = 2x` 时把自己和自己配对。
'''},

{"cat": "hash", "lc": 49, "t": "字母异位词分组", "d": "中等", "slug": "group-anagrams", "md": r'''
**题目**：给一个字符串数组，把「字母异位词」（字母相同、顺序不同的词，如 eat/tea/ate）分到同一组。

**举例**：`["eat","tea","tan","ate","nat","bat"]` → `[["eat","tea","ate"],["tan","nat"],["bat"]]`

#### 💡 思路（白话）

- 分组问题的套路：**给每组找一个唯一的「身份证」（key），key 相同的进同一组**。
- 异位词的特点：把字母排序后结果一样。`eat`、`tea`、`ate` 排序后都是 `aet`——这就是天然的 key！
- 做法：准备一个 map（key → 这组的单词列表）。每个单词排序得到 key，塞进对应的组。最后把 map 的所有 value 收集起来返回。

#### ☕ Java

```java
class Solution {
    public List<List<String>> groupAnagrams(String[] strs) {
        Map<String, List<String>> groups = new HashMap<>();
        for (String s : strs) {
            char[] cs = s.toCharArray();
            Arrays.sort(cs);                  // "eat" -> "aet"，作为身份证
            String key = new String(cs);
            groups.computeIfAbsent(key, k -> new ArrayList<>()).add(s);
        }
        return new ArrayList<>(groups.values());
    }
}
```

#### 🐍 Python

```python
class Solution:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        groups = defaultdict(list)
        for s in strs:
            key = ''.join(sorted(s))   # 排序后的字符串作 key
            groups[key].append(s)
        return list(groups.values())
```

#### ⏱ 复杂度

时间 O(n · k log k)（n 个单词，每个长 k 要排序），空间 O(n · k)。

**小白提示**：学会 `computeIfAbsent`（Java）/ `defaultdict(list)`（Python），「不存在就先建空列表再添加」一行搞定，分组题全靠它。
'''},

{"cat": "hash", "lc": 128, "t": "最长连续序列", "d": "中等", "slug": "longest-consecutive-sequence", "md": r'''
**题目**：给一个**未排序**的数组，找出数字连续（如 1,2,3,4）的最长序列长度。要求 O(n)，所以不能排序。

**举例**：`[100,4,200,1,3,2]` → 最长连续序列是 `1,2,3,4`，返回 4。

#### 💡 思路（白话）

- 先把所有数丢进 set（去重 + O(1) 查询）。
- 对每个数 `x`，往后数 `x+1, x+2…` 在不在 set 里，能数多长就是一条序列。
- 但这样会重复数：对 `1,2,3,4`，从 2、3、4 出发都是白干。**关键优化：只从「序列起点」出发**——`x` 是起点，当且仅当 `x-1` 不在 set 里。
- 这样每个数最多被访问两次，总体 O(n)。

#### ☕ Java

```java
class Solution {
    public int longestConsecutive(int[] nums) {
        Set<Integer> set = new HashSet<>();
        for (int x : nums) set.add(x);
        int best = 0;
        for (int x : set) {
            if (set.contains(x - 1)) continue; // 不是起点，跳过
            int cur = x, len = 1;
            while (set.contains(cur + 1)) {    // 从起点一路往后数
                cur++; len++;
            }
            best = Math.max(best, len);
        }
        return best;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def longestConsecutive(self, nums: List[int]) -> int:
        s = set(nums)
        best = 0
        for x in s:
            if x - 1 in s:          # 不是起点
                continue
            cur = x
            while cur + 1 in s:
                cur += 1
            best = max(best, cur - x + 1)
        return best
```

#### ⏱ 复杂度

时间 O(n)，空间 O(n)。

**小白提示**：`if x-1 in s: continue` 这行是本题的灵魂——没有它就退化成 O(n²) 超时。遍历 set 而不是原数组，可以顺便跳过重复元素。
'''},

{"cat": "two-pointers", "lc": 283, "t": "移动零", "d": "简单", "slug": "move-zeroes", "md": r'''
**题目**：把数组中所有 0 移到末尾，**保持非零元素的相对顺序**，必须原地操作（不能新建数组）。

**举例**：`[0,1,0,3,12]` → `[1,3,12,0,0]`

#### 💡 思路（白话）

- 快慢指针：`slow` 指向「下一个非零元素该放的位置」，`fast` 从头到尾扫。
- `fast` 遇到非零数，就放到 `slow` 的位置，`slow` 前进一格；遇到 0 什么都不做。
- 扫完后，`slow` 之前全是按原顺序排好的非零数，把 `slow` 到末尾全部填 0 即可。
- 直观理解：`slow` 是「收纳员」，`fast` 是「搬运工」，搬运工只把非零的货递给收纳员。

#### ☕ Java

```java
class Solution {
    public void moveZeroes(int[] nums) {
        int slow = 0;
        for (int fast = 0; fast < nums.length; fast++) {
            if (nums[fast] != 0) {
                nums[slow++] = nums[fast];   // 非零数往前放
            }
        }
        while (slow < nums.length) {
            nums[slow++] = 0;                // 剩下的位置补 0
        }
    }
}
```

#### 🐍 Python

```python
class Solution:
    def moveZeroes(self, nums: List[int]) -> None:
        slow = 0
        for fast in range(len(nums)):
            if nums[fast] != 0:
                nums[slow] = nums[fast]
                slow += 1
        for i in range(slow, len(nums)):
            nums[i] = 0
```

#### ⏱ 复杂度

时间 O(n)，空间 O(1)。

**小白提示**：这是快慢指针最干净的入门题。同样的写法稍改判断条件，就能做「删除有序数组中的重复项」（LC 26）——一题会，一类会。
'''},

{"cat": "two-pointers", "lc": 11, "t": "盛最多水的容器", "d": "中等", "slug": "container-with-most-water", "md": r'''
**题目**：数组每个元素代表一根竖线的高度，选两根线和 x 轴围成容器，求最多能装多少水。

**举例**：`[1,8,6,2,5,4,8,3,7]` → 选下标 1（高 8）和 8（高 7），面积 = min(8,7) × (8-1) = 49。

#### 💡 思路（白话）

- 容量 = **两线中较矮的那根** × 两线间距。
- 对撞指针：`left` 在最左、`right` 在最右（间距最大），算一次面积。
- 然后**移动较矮的那根**。为什么？间距在缩小，想让面积变大只能指望高度变高；而高度由矮的决定——动高的那根，矮的还在，高度不可能变高，面积只会更小。所以动矮的才有希望。
- 每步记录最大面积，指针相遇结束。

#### ☕ Java

```java
class Solution {
    public int maxArea(int[] height) {
        int left = 0, right = height.length - 1, best = 0;
        while (left < right) {
            int area = Math.min(height[left], height[right]) * (right - left);
            best = Math.max(best, area);
            if (height[left] < height[right]) left++;   // 移动矮的那根
            else right--;
        }
        return best;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def maxArea(self, height: List[int]) -> int:
        left, right, best = 0, len(height) - 1, 0
        while left < right:
            best = max(best, min(height[left], height[right]) * (right - left))
            if height[left] < height[right]:
                left += 1
            else:
                right -= 1
        return best
```

#### ⏱ 复杂度

时间 O(n)，空间 O(1)。

**小白提示**：面试常追问「为什么移动矮的不会错过最优解？」答：固定矮的那根时，它和**任何**更近的线组合面积都不会超过当前值，所以可以放心淘汰它。
'''},

{"cat": "two-pointers", "lc": 15, "t": "三数之和", "d": "中等", "slug": "3sum", "md": r'''
**题目**：找出数组中所有「和为 0 的三元组」，**结果不能有重复的三元组**。

**举例**：`[-1,0,1,2,-1,-4]` → `[[-1,-1,2],[-1,0,1]]`

#### 💡 思路（白话）

- 先**排序**（去重和双指针都靠它）。
- 固定第一个数 `nums[i]`，问题变成「在 i 右边找两个数，和为 `-nums[i]`」——有序数组找两数之和，用对撞指针：和太小 `left++`，太大 `right--`。
- **去重三处**：① `i` 跳过和前一个相同的值；② 找到一组解后，`left`、`right` 各自跳过相同值。
- 小剪枝：`nums[i] > 0` 时直接 break（最小的数都大于 0，不可能凑出 0）。

#### ☕ Java

```java
class Solution {
    public List<List<Integer>> threeSum(int[] nums) {
        Arrays.sort(nums);
        List<List<Integer>> res = new ArrayList<>();
        for (int i = 0; i < nums.length - 2; i++) {
            if (nums[i] > 0) break;                        // 剪枝
            if (i > 0 && nums[i] == nums[i - 1]) continue; // 第一个数去重
            int left = i + 1, right = nums.length - 1;
            while (left < right) {
                int sum = nums[i] + nums[left] + nums[right];
                if (sum < 0) left++;
                else if (sum > 0) right--;
                else {
                    res.add(List.of(nums[i], nums[left], nums[right]));
                    while (left < right && nums[left] == nums[left + 1]) left++;   // 去重
                    while (left < right && nums[right] == nums[right - 1]) right--; // 去重
                    left++; right--;
                }
            }
        }
        return res;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def threeSum(self, nums: List[int]) -> List[List[int]]:
        nums.sort()
        res = []
        for i in range(len(nums) - 2):
            if nums[i] > 0: break
            if i > 0 and nums[i] == nums[i - 1]: continue
            left, right = i + 1, len(nums) - 1
            while left < right:
                s = nums[i] + nums[left] + nums[right]
                if s < 0: left += 1
                elif s > 0: right -= 1
                else:
                    res.append([nums[i], nums[left], nums[right]])
                    while left < right and nums[left] == nums[left + 1]: left += 1
                    while left < right and nums[right] == nums[right - 1]: right -= 1
                    left += 1; right -= 1
        return res
```

#### ⏱ 复杂度

时间 O(n²)，空间 O(1)（不算结果）。

**小白提示**：本题难点不在双指针，在**去重**——三处去重一处都不能少，建议拿 `[-1,-1,-1,0,1,2]` 在纸上走一遍。
'''},

{"cat": "two-pointers", "lc": 42, "t": "接雨水", "d": "困难", "slug": "trapping-rain-water", "md": r'''
**题目**：数组表示柱子高度，下雨后这些柱子之间能接多少水？

**举例**：`[0,1,0,2,1,0,1,3,2,1,2,1]` → 返回 6。

#### 💡 思路（白话）

- **核心公式**：每个位置 `i` 上方能存的水 = `min(左边最高, 右边最高) - 自己的高度`（负数记 0）。想象位置 i 是个水桶，水位由左右两边的「最高挡板」中较矮的决定。
- 朴素法：先两遍预处理出每个位置的 `leftMax[]`、`rightMax[]`，再扫一遍求和，O(n) 时间 O(n) 空间——**先把这个写会**。
- 双指针优化（O(1) 空间）：左右各一个指针，各自维护 `leftMax`、`rightMax`。若 `leftMax < rightMax`，左指针位置的水量已确定（短板在左边），结算并右移；反之处理右指针。

#### ☕ Java

```java
class Solution {
    public int trap(int[] height) {
        int left = 0, right = height.length - 1;
        int leftMax = 0, rightMax = 0, water = 0;
        while (left < right) {
            leftMax = Math.max(leftMax, height[left]);
            rightMax = Math.max(rightMax, height[right]);
            if (leftMax < rightMax) {        // 短板在左边，左边水量可结算
                water += leftMax - height[left];
                left++;
            } else {
                water += rightMax - height[right];
                right--;
            }
        }
        return water;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def trap(self, height: List[int]) -> int:
        left, right = 0, len(height) - 1
        left_max = right_max = water = 0
        while left < right:
            left_max = max(left_max, height[left])
            right_max = max(right_max, height[right])
            if left_max < right_max:
                water += left_max - height[left]
                left += 1
            else:
                water += right_max - height[right]
                right -= 1
        return water
```

#### ⏱ 复杂度

时间 O(n)，空间 O(1)。

**小白提示**：困难题不用怕——先把「每格水 = min(左最高, 右最高) − 自身」这个公式想通（画个图一目了然），预处理数组版完全够面试用，双指针版是加分项。
'''},

{"cat": "sliding-window", "lc": 3, "t": "无重复字符的最长子串", "d": "中等", "slug": "longest-substring-without-repeating-characters", "md": r'''
**题目**：找出字符串中**不含重复字符**的最长子串的长度。

**举例**：`"abcabcbb"` → 最长是 `"abc"`，返回 3。

#### 💡 思路（白话）

- 滑动窗口模板的标准应用。窗口 `[left, right]` 内保证没有重复字符。
- `right` 每右移一格，把新字符加入窗口（用 set 或计数 map 记录）。
- 如果新字符在窗口里已经有了（窗口「不合法」了），就不断把 `left` 的字符移出窗口、`left++`，直到重复消失。
- 每轮用窗口长度 `right - left + 1` 更新答案。
- 两个指针都只往右走，每个字符最多进出窗口一次，O(n)。

#### ☕ Java

```java
class Solution {
    public int lengthOfLongestSubstring(String s) {
        Set<Character> window = new HashSet<>();
        int left = 0, best = 0;
        for (int right = 0; right < s.length(); right++) {
            char c = s.charAt(right);
            while (window.contains(c)) {      // 出现重复 → 收缩左边
                window.remove(s.charAt(left));
                left++;
            }
            window.add(c);
            best = Math.max(best, right - left + 1);
        }
        return best;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        window = set()
        left = best = 0
        for right, c in enumerate(s):
            while c in window:
                window.remove(s[left])
                left += 1
            window.add(c)
            best = max(best, right - left + 1)
        return best
```

#### ⏱ 复杂度

时间 O(n)，空间 O(字符集大小)。

**小白提示**：这是滑动窗口的「Hello World」，把它写到闭着眼也不出错。注意 while 里移除的是 `s[left]`（左端字符）而不是 `c`，初学最容易写反。
'''},

{"cat": "sliding-window", "lc": 438, "t": "找到字符串中所有字母异位词", "d": "中等", "slug": "find-all-anagrams-in-a-string", "md": r'''
**题目**：在字符串 `s` 中找到所有 `p` 的异位词（字母相同顺序不同）子串，返回起始下标。

**举例**：`s = "cbaebabacd", p = "abc"` → 返回 `[0,6]`（`"cba"` 和 `"bac"`）。

#### 💡 思路（白话）

- 异位词长度固定等于 `p` 的长度 → **定长滑动窗口**：窗口大小始终是 `len(p)`，每次右进一个字符、左出一个字符。
- 怎么判断窗口是 p 的异位词？比较**字母出现次数**是否完全一样。只有小写字母，用长度 26 的数组计数即可。
- 流程：先统计 p 的计数 `need`；窗口每滑一步更新自己的计数 `window`，两数组相等就记录 `left`。

#### ☕ Java

```java
class Solution {
    public List<Integer> findAnagrams(String s, String p) {
        List<Integer> res = new ArrayList<>();
        if (s.length() < p.length()) return res;
        int[] need = new int[26], window = new int[26];
        for (char c : p.toCharArray()) need[c - 'a']++;
        for (int right = 0; right < s.length(); right++) {
            window[s.charAt(right) - 'a']++;            // 右端进
            int left = right - p.length() + 1;
            if (left > 0) window[s.charAt(left - 1) - 'a']--; // 左端出
            if (left >= 0 && Arrays.equals(need, window)) res.add(left);
        }
        return res;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def findAnagrams(self, s: str, p: str) -> List[int]:
        if len(s) < len(p): return []
        need, window = Counter(p), Counter(s[:len(p)])
        res = [0] if need == window else []
        for right in range(len(p), len(s)):
            window[s[right]] += 1              # 右端进
            left_ch = s[right - len(p)]
            window[left_ch] -= 1               # 左端出
            if window[left_ch] == 0:
                del window[left_ch]            # Counter 比较前删掉 0 项
            if window == need:
                res.append(right - len(p) + 1)
        return res
```

#### ⏱ 复杂度

时间 O(n × 26) ≈ O(n)，空间 O(26)。

**小白提示**：「定长窗口」比通用模板更简单——每步固定一进一出，不需要 while 收缩。看到「找长度为 k 的满足 xx 的子串」就往这套。
'''},
]
