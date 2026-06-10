# LeetCode Hot 100 讲义 · Part 3：链表(14)
PROBLEMS = [
{"cat": "linked-list", "lc": 160, "t": "相交链表", "d": "简单", "slug": "intersection-of-two-linked-lists", "md": r'''
**题目**：找出两个单链表的相交起始节点（相交后两条链表完全重合），不相交返回 null。

#### 💡 思路（白话）

- 浪漫解法「走过你走过的路」：指针 A 从链表 A 出发，走到尾就跳到链表 B 的头；指针 B 同理跳到 A 的头。
- 为什么能相遇？设 A 独有部分长 a、B 独有部分长 b、公共部分长 c。指针 A 走 `a + c + b` 步、指针 B 走 `b + c + a` 步后，**都恰好到达交点**——走的总路程相同！
- 不相交时，两指针会同时走到 null（`a+c+b = b+c+a` 仍成立），循环正常结束返回 null。

#### ☕ Java

```java
public class Solution {
    public ListNode getIntersectionNode(ListNode headA, ListNode headB) {
        ListNode pa = headA, pb = headB;
        while (pa != pb) {
            pa = (pa == null) ? headB : pa.next;  // 走完自己的路走对方的
            pb = (pb == null) ? headA : pb.next;
        }
        return pa;   // 交点或 null
    }
}
```

#### 🐍 Python

```python
class Solution:
    def getIntersectionNode(self, headA: ListNode, headB: ListNode) -> Optional[ListNode]:
        pa, pb = headA, headB
        while pa is not pb:
            pa = headB if pa is None else pa.next
            pb = headA if pb is None else pb.next
        return pa
```

#### ⏱ 复杂度

时间 O(m+n)，空间 O(1)。

**小白提示**：跳转条件是 `pa == null` 时跳，而不是 `pa.next == null` 时跳——后者在不相交时会死循环。想不通就用「土办法」：先各遍历一遍算长度，长的先走差值步，再一起走。
'''},

{"cat": "linked-list", "lc": 206, "t": "反转链表", "d": "简单", "slug": "reverse-linked-list", "md": r'''
**题目**：反转单链表。`1→2→3→4→5` 变成 `5→4→3→2→1`。

#### 💡 思路（白话）

- 三个指针走天下：`prev`（已反转部分的头，初始 null）、`cur`（当前处理的节点）、`nxt`（先存好下一个，防止断链后找不到）。
- 每一步做四件事，**顺序不能乱**：
  1. `nxt = cur.next`（备份下一个）
  2. `cur.next = prev`（箭头掉头！）
  3. `prev = cur`（prev 前进）
  4. `cur = nxt`（cur 前进）
- `cur` 走到 null 时，`prev` 就是新头。

#### ☕ Java

```java
class Solution {
    public ListNode reverseList(ListNode head) {
        ListNode prev = null, cur = head;
        while (cur != null) {
            ListNode nxt = cur.next;  // 1. 备份
            cur.next = prev;          // 2. 掉头
            prev = cur;               // 3. prev 前进
            cur = nxt;                // 4. cur 前进
        }
        return prev;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def reverseList(self, head: Optional[ListNode]) -> Optional[ListNode]:
        prev, cur = None, head
        while cur:
            cur.next, prev, cur = prev, cur, cur.next  # 一行完成四步
        return prev
```

#### ⏱ 复杂度

时间 O(n)，空间 O(1)。

**小白提示**：这是链表题的「基本功中的基本功」，K 个一组翻转、回文链表都要用它。务必在纸上画 3 个节点跟着代码走一遍，把「先备份再掉头」刻进肌肉记忆。
'''},

{"cat": "linked-list", "lc": 234, "t": "回文链表", "d": "简单", "slug": "palindrome-linked-list", "md": r'''
**题目**：判断链表是否是回文（正读反读一样），如 `1→2→2→1`。进阶要求 O(n) 时间、O(1) 空间。

#### 💡 思路（白话）

- 简单做法：遍历存进数组，双指针判回文——O(n) 空间，先会这个。
- O(1) 空间做法 = 三个基本功的组合拳：
  1. **快慢指针找中点**：快的一次两步，快的到尾时慢的在中间；
  2. **反转后半段**；
  3. **两头同时比对**，全相等就是回文。

#### ☕ Java

```java
class Solution {
    public boolean isPalindrome(ListNode head) {
        ListNode slow = head, fast = head;
        while (fast != null && fast.next != null) {   // 1. 找中点
            slow = slow.next;
            fast = fast.next.next;
        }
        ListNode prev = null, cur = slow;             // 2. 反转后半段
        while (cur != null) {
            ListNode nxt = cur.next;
            cur.next = prev;
            prev = cur; cur = nxt;
        }
        ListNode p1 = head, p2 = prev;                // 3. 双向比对
        while (p2 != null) {
            if (p1.val != p2.val) return false;
            p1 = p1.next; p2 = p2.next;
        }
        return true;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def isPalindrome(self, head: Optional[ListNode]) -> bool:
        vals = []                      # 数组法，简单直接
        while head:
            vals.append(head.val)
            head = head.next
        return vals == vals[::-1]
```

#### ⏱ 复杂度

时间 O(n)；空间：数组法 O(n)，反转法 O(1)。

**小白提示**：奇数长度时中间节点归前半段还是后半段都行，比对以后半段走完为准，不影响结果。面试先口述数组法，再写反转法展示基本功。
'''},

{"cat": "linked-list", "lc": 141, "t": "环形链表", "d": "简单", "slug": "linked-list-cycle", "md": r'''
**题目**：判断链表中是否有环（尾节点的 next 指回了前面的某个节点）。

#### 💡 思路（白话）

- **快慢指针（Floyd 判圈）**：慢指针一次一步，快指针一次两步。
- 没环：快指针先到达 null，结束。
- 有环：两个指针迟早都进环，环里快的每轮比慢的多走一步，相当于「操场跑圈，快的一定能套圈追上慢的」→ 相遇即有环。

#### ☕ Java

```java
public class Solution {
    public boolean hasCycle(ListNode head) {
        ListNode slow = head, fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
            if (slow == fast) return true;   // 追上了 → 有环
        }
        return false;                        // 快指针到头了 → 无环
    }
}
```

#### 🐍 Python

```python
class Solution:
    def hasCycle(self, head: Optional[ListNode]) -> bool:
        slow = fast = head
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
            if slow is fast:
                return True
        return False
```

#### ⏱ 复杂度

时间 O(n)，空间 O(1)。

**小白提示**：循环条件 `fast != null && fast.next != null` 两个判断缺一不可（fast 一次走两步，要保证两步都不踩空）。比较用 `==`（同一个节点对象），不是比较值。
'''},

{"cat": "linked-list", "lc": 142, "t": "环形链表 II", "d": "中等", "slug": "linked-list-cycle-ii", "md": r'''
**题目**：如果链表有环，返回**入环的第一个节点**；无环返回 null。

#### 💡 思路（白话）

- 第一步同上题：快慢指针，相遇说明有环。
- 第二步是数学魔法：**相遇后，把一个指针放回头节点，两个指针都改为一次一步，再次相遇的位置就是环入口**。
- 为什么？设头到入口距离 a，入口到相遇点 b，相遇点绕回入口 c。相遇时慢走了 `a+b`，快走了 `a+b+n(b+c)`，又因为快是慢的 2 倍：`a+b = n(b+c)`，推出 `a = c + (n-1)(b+c)`——从头走 a 步和从相遇点走 c 步（多绕几圈）会在入口碰头。

#### ☕ Java

```java
public class Solution {
    public ListNode detectCycle(ListNode head) {
        ListNode slow = head, fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
            if (slow == fast) {              // 相遇，有环
                ListNode p = head;           // 一个回到头
                while (p != slow) {          // 同速前进
                    p = p.next;
                    slow = slow.next;
                }
                return p;                    // 入口
            }
        }
        return null;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def detectCycle(self, head: Optional[ListNode]) -> Optional[ListNode]:
        slow = fast = head
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
            if slow is fast:
                p = head
                while p is not slow:
                    p = p.next
                    slow = slow.next
                return p
        return None
```

#### ⏱ 复杂度

时间 O(n)，空间 O(1)。

**小白提示**：推导记不住没关系，**结论必须记住**：「相遇后一个回起点，同速走，再相遇即入口」。后面「寻找重复数」会原封不动地再用一次。
'''},

{"cat": "linked-list", "lc": 21, "t": "合并两个有序链表", "d": "简单", "slug": "merge-two-sorted-lists", "md": r'''
**题目**：合并两个升序链表，返回新的升序链表。`1→2→4` + `1→3→4` → `1→1→2→3→4→4`。

#### 💡 思路（白话）

- 像拉拉链：两个链表头比一比，谁小谁接到结果上，对应指针前进一步，直到一边用完，把另一边整条接上。
- **虚拟头节点 dummy** 登场：先放一个假头，往后挂节点，最后返回 `dummy.next`。免去「第一个节点要特判」的麻烦——这个技巧后面无数链表题都要用。

#### ☕ Java

```java
class Solution {
    public ListNode mergeTwoLists(ListNode l1, ListNode l2) {
        ListNode dummy = new ListNode(0);   // 虚拟头
        ListNode tail = dummy;
        while (l1 != null && l2 != null) {
            if (l1.val <= l2.val) { tail.next = l1; l1 = l1.next; }
            else                  { tail.next = l2; l2 = l2.next; }
            tail = tail.next;
        }
        tail.next = (l1 != null) ? l1 : l2;  // 接上剩余部分
        return dummy.next;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def mergeTwoLists(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        dummy = tail = ListNode(0)
        while l1 and l2:
            if l1.val <= l2.val:
                tail.next, l1 = l1, l1.next
            else:
                tail.next, l2 = l2, l2.next
            tail = tail.next
        tail.next = l1 or l2
        return dummy.next
```

#### ⏱ 复杂度

时间 O(m+n)，空间 O(1)。

**小白提示**：这题是「合并 K 个升序链表」和「排序链表」的零件，必须熟练。记住 dummy 模式三件套：建 dummy → tail 往后挂 → 返回 `dummy.next`。
'''},

{"cat": "linked-list", "lc": 2, "t": "两数相加", "d": "中等", "slug": "add-two-numbers", "md": r'''
**题目**：两个链表逆序存两个数（个位在前），求和并以同样形式返回。`2→4→3`（342）+ `5→6→4`（465）→ `7→0→8`（807）。

#### 💡 思路（白话）

- 就是小学竖式加法！逆序存储反而方便——从链表头开始加正好是从个位加起。
- 每一位：`sum = l1的值 + l2的值 + 进位carry`，本位是 `sum % 10`，新进位是 `sum / 10`。
- 循环条件：`l1、l2 还有节点，或 carry 还有进位`（如 99+1 最后要多出一位），三者统一处理，短的链表当 0。

#### ☕ Java

```java
class Solution {
    public ListNode addTwoNumbers(ListNode l1, ListNode l2) {
        ListNode dummy = new ListNode(0), tail = dummy;
        int carry = 0;
        while (l1 != null || l2 != null || carry != 0) {
            int sum = carry;
            if (l1 != null) { sum += l1.val; l1 = l1.next; }
            if (l2 != null) { sum += l2.val; l2 = l2.next; }
            tail.next = new ListNode(sum % 10);  // 本位
            carry = sum / 10;                    // 进位
            tail = tail.next;
        }
        return dummy.next;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        dummy = tail = ListNode(0)
        carry = 0
        while l1 or l2 or carry:
            s = carry + (l1.val if l1 else 0) + (l2.val if l2 else 0)
            tail.next = ListNode(s % 10)
            carry = s // 10
            tail = tail.next
            l1 = l1.next if l1 else None
            l2 = l2.next if l2 else None
        return dummy.next
```

#### ⏱ 复杂度

时间 O(max(m,n))，空间 O(1)（不算结果链表）。

**小白提示**：把 `carry != 0` 放进循环条件，就不用在循环外单独处理「最高位进位」，少一个 if 少一个 bug。
'''},

{"cat": "linked-list", "lc": 19, "t": "删除链表的倒数第 N 个结点", "d": "中等", "slug": "remove-nth-node-from-end-of-list", "md": r'''
**题目**：一趟扫描删除链表的倒数第 n 个节点。

#### 💡 思路（白话）

- **前后指针**：让 `fast` 先走 n+1 步，然后 `fast`、`slow` 一起走。`fast` 到 null 时，`slow` 恰好停在**被删节点的前一个**，执行 `slow.next = slow.next.next` 即可。
- 为什么从 dummy 出发、先走 n+1 步？要删的可能是头节点（如链表长 n、删倒数第 n 个），有 dummy 就不用特判。

#### ☕ Java

```java
class Solution {
    public ListNode removeNthFromEnd(ListNode head, int n) {
        ListNode dummy = new ListNode(0, head);
        ListNode fast = dummy, slow = dummy;
        for (int i = 0; i <= n; i++) fast = fast.next;  // 先走 n+1 步
        while (fast != null) {
            fast = fast.next;
            slow = slow.next;
        }
        slow.next = slow.next.next;   // slow 停在被删节点前一个
        return dummy.next;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def removeNthFromEnd(self, head: Optional[ListNode], n: int) -> Optional[ListNode]:
        dummy = ListNode(0, head)
        fast = slow = dummy
        for _ in range(n + 1):
            fast = fast.next
        while fast:
            fast = fast.next
            slow = slow.next
        slow.next = slow.next.next
        return dummy.next
```

#### ⏱ 复杂度

时间 O(n)，空间 O(1)。

**小白提示**：删除节点的关键是拿到**前一个**节点，所以 slow 要停在被删节点之前——这就是「先走 n+1 步而不是 n 步」的原因。测试用例记得跑「删头节点」`[1], n=1`。
'''},

{"cat": "linked-list", "lc": 24, "t": "两两交换链表中的节点", "d": "中等", "slug": "swap-nodes-in-pairs", "md": r'''
**题目**：两两交换相邻节点。`1→2→3→4` → `2→1→4→3`（必须换节点，不能只换值）。

#### 💡 思路（白话）

- 用 dummy + `prev` 指针，每轮处理一对。设这对是 `a → b`，要变成 `prev → b → a → 下一对`：
  1. `prev.next = b`
  2. `a.next = b.next`
  3. `b.next = a`
  4. `prev = a`（a 现在是这对的尾巴，作为下一轮的 prev）
- 在纸上画 4 个节点 + 3 根箭头，按顺序改一遍立刻就懂。

#### ☕ Java

```java
class Solution {
    public ListNode swapPairs(ListNode head) {
        ListNode dummy = new ListNode(0, head);
        ListNode prev = dummy;
        while (prev.next != null && prev.next.next != null) {
            ListNode a = prev.next, b = a.next;
            prev.next = b;       // prev -> b
            a.next = b.next;     // a -> 下一对
            b.next = a;          // b -> a
            prev = a;            // a 成了这对的尾
        }
        return dummy.next;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def swapPairs(self, head: Optional[ListNode]) -> Optional[ListNode]:
        dummy = ListNode(0, head)
        prev = dummy
        while prev.next and prev.next.next:
            a, b = prev.next, prev.next.next
            prev.next, a.next, b.next = b, b.next, a
            prev = a
        return dummy.next
```

#### ⏱ 复杂度

时间 O(n)，空间 O(1)。

**小白提示**：这是「K 个一组翻转」的 k=2 特例，先把它写顺。循环条件保证「还凑得齐一对」，奇数个节点的最后一个自动保持原样。
'''},

{"cat": "linked-list", "lc": 25, "t": "K 个一组翻转链表", "d": "困难", "slug": "reverse-nodes-in-k-group", "md": r'''
**题目**：每 k 个节点一组翻转链表，不足 k 个的尾部保持原样。`1→2→3→4→5, k=2` → `2→1→4→3→5`。

#### 💡 思路（白话）

- 拆成你已会的两件事：**反转链表**（206 题）+ **分组处理**。
- 每一轮：
  1. 从 `prevGroupEnd`（上一组的尾巴，初始为 dummy）往后数 k 个，不够就结束；
  2. 把这 k 个节点用「反转链表」翻转；
  3. **重新接好两端**：上一组尾巴接新头，新尾巴（翻转前的头）接下一组的开头；
  4. `prevGroupEnd` 移到本组新尾巴。

#### ☕ Java

```java
class Solution {
    public ListNode reverseKGroup(ListNode head, int k) {
        ListNode dummy = new ListNode(0, head);
        ListNode prevGroupEnd = dummy;
        while (true) {
            ListNode kth = prevGroupEnd;            // 1. 找本组第 k 个
            for (int i = 0; i < k && kth != null; i++) kth = kth.next;
            if (kth == null) break;                 // 不足 k 个，结束
            ListNode groupStart = prevGroupEnd.next;
            ListNode nextGroup = kth.next;
            ListNode prev = nextGroup, cur = groupStart;  // 2. 翻转本组
            while (cur != nextGroup) {              // 尾巴直接指向下一组
                ListNode nxt = cur.next;
                cur.next = prev;
                prev = cur; cur = nxt;
            }
            prevGroupEnd.next = kth;                // 3. 上一组接新头
            prevGroupEnd = groupStart;              // 4. 原头变新尾
        }
        return dummy.next;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def reverseKGroup(self, head: Optional[ListNode], k: int) -> Optional[ListNode]:
        dummy = ListNode(0, head)
        prev_group_end = dummy
        while True:
            kth = prev_group_end
            for _ in range(k):
                kth = kth.next
                if not kth: return dummy.next
            group_start, next_group = prev_group_end.next, kth.next
            prev, cur = next_group, group_start    # 翻转，尾直接指向下一组
            while cur is not next_group:
                cur.next, prev, cur = prev, cur, cur.next
            prev_group_end.next = kth
            prev_group_end = group_start
        return dummy.next
```

#### ⏱ 复杂度

时间 O(n)，空间 O(1)。

**小白提示**：初始化 `prev = nextGroup`（而不是 null）是个小妙招——翻转完成时本组尾巴自动接上下一组，省一步。这题是字节等大厂手撕代码的最高频题之一，值得反复写。
'''},

{"cat": "linked-list", "lc": 138, "t": "随机链表的复制", "d": "中等", "slug": "copy-list-with-random-pointer", "md": r'''
**题目**：链表每个节点除了 next 还有一个 `random` 指针（指向任意节点或 null），深拷贝整个链表。

#### 💡 思路（白话）

- 难点：复制 `random` 时，它指向的新节点可能还没创建。
- **哈希表两遍法**（推荐）：
  1. 第一遍：为每个旧节点创建对应新节点，存入 map（旧 → 新）；
  2. 第二遍：`新.next = map(旧.next)`，`新.random = map(旧.random)`——map 帮你把「旧世界的关系」翻译成「新世界的关系」。

#### ☕ Java

```java
class Solution {
    public Node copyRandomList(Node head) {
        Map<Node, Node> map = new HashMap<>();     // 旧 -> 新
        for (Node p = head; p != null; p = p.next)
            map.put(p, new Node(p.val));
        for (Node p = head; p != null; p = p.next) {
            map.get(p).next = map.get(p.next);     // map.get(null) 恰好是 null
            map.get(p).random = map.get(p.random);
        }
        return map.get(head);
    }
}
```

#### 🐍 Python

```python
class Solution:
    def copyRandomList(self, head: 'Optional[Node]') -> 'Optional[Node]':
        mapping = {None: None}                 # 让 None 也能查
        p = head
        while p:
            mapping[p] = Node(p.val)
            p = p.next
        p = head
        while p:
            mapping[p].next = mapping[p.next]
            mapping[p].random = mapping[p.random]
            p = p.next
        return mapping[head]
```

#### ⏱ 复杂度

时间 O(n)，空间 O(n)。

**小白提示**：Python 里预放 `{None: None}`（Java 的 `map.get(null)` 本来就返回 null）就不用判空。O(1) 空间的「节点交织法」（新节点插在旧节点后面）可作课后了解，面试说出哈希表法就合格。
'''},

{"cat": "linked-list", "lc": 148, "t": "排序链表", "d": "中等", "slug": "sort-list", "md": r'''
**题目**：对链表升序排序，要求 O(n log n) 时间。

#### 💡 思路（白话）

- O(n log n) 的排序：快排、堆排、归并。链表不能随机访问，**归并排序**最合适——它只需要顺序遍历，而且链表合并不需要额外数组。
- 递归三步（全是学过的零件）：
  1. **快慢指针找中点**，从中间断开成两半；
  2. 递归排序左半、右半；
  3. **合并两个有序链表**（21 题原题）。

#### ☕ Java

```java
class Solution {
    public ListNode sortList(ListNode head) {
        if (head == null || head.next == null) return head;
        ListNode slow = head, fast = head.next;   // fast 先一步，保证从中间偏左断开
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
        }
        ListNode mid = slow.next;
        slow.next = null;                          // 断开！
        ListNode left = sortList(head), right = sortList(mid);
        ListNode dummy = new ListNode(0), tail = dummy;  // 合并两个有序链表
        while (left != null && right != null) {
            if (left.val <= right.val) { tail.next = left; left = left.next; }
            else                       { tail.next = right; right = right.next; }
            tail = tail.next;
        }
        tail.next = (left != null) ? left : right;
        return dummy.next;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def sortList(self, head: Optional[ListNode]) -> Optional[ListNode]:
        if not head or not head.next:
            return head
        slow, fast = head, head.next
        while fast and fast.next:
            slow, fast = slow.next, fast.next.next
        mid, slow.next = slow.next, None        # 从中点断开
        left, right = self.sortList(head), self.sortList(mid)
        dummy = tail = ListNode(0)
        while left and right:
            if left.val <= right.val:
                tail.next, left = left, left.next
            else:
                tail.next, right = right, right.next
            tail = tail.next
        tail.next = left or right
        return dummy.next
```

#### ⏱ 复杂度

时间 O(n log n)，空间 O(log n)（递归栈）。

**小白提示**：`fast = head.next` 起步（比 slow 先一步）能保证两个节点时正确断成 1+1；写成 `fast = head` 会死循环——这是本题第一坑。
'''},

{"cat": "linked-list", "lc": 23, "t": "合并 K 个升序链表", "d": "困难", "slug": "merge-k-sorted-lists", "md": r'''
**题目**：合并 k 个升序链表为一个升序链表。

#### 💡 思路（白话）

- 每次要从 k 个链表头里挑最小的——「动态取最小」正是**小顶堆**的拿手活。
- 流程：k 个链表的头节点全部入堆 → 弹出最小的接到结果上 → 它的 next（如果有）补进堆 → 重复到堆空。
- 另一种思路「分治两两合并」（像归并排序）复杂度相同，堆法更好写。

#### ☕ Java

```java
class Solution {
    public ListNode mergeKLists(ListNode[] lists) {
        PriorityQueue<ListNode> heap = new PriorityQueue<>((a, b) -> a.val - b.val);
        for (ListNode head : lists)
            if (head != null) heap.offer(head);
        ListNode dummy = new ListNode(0), tail = dummy;
        while (!heap.isEmpty()) {
            ListNode node = heap.poll();      // 当前 k 个头里最小的
            tail.next = node;
            tail = node;
            if (node.next != null) heap.offer(node.next);  // 补位
        }
        return dummy.next;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def mergeKLists(self, lists: List[Optional[ListNode]]) -> Optional[ListNode]:
        heap = []
        for i, head in enumerate(lists):
            if head:
                heapq.heappush(heap, (head.val, i, head))  # i 防止 val 相同时比较节点报错
        dummy = tail = ListNode(0)
        while heap:
            _, i, node = heapq.heappop(heap)
            tail.next = node
            tail = node
            if node.next:
                heapq.heappush(heap, (node.next.val, i, node.next))
        return dummy.next
```

#### ⏱ 复杂度

时间 O(N log k)（N 是总节点数，堆大小只有 k），空间 O(k)。

**小白提示**：Python 的堆元组里夹一个序号 `i` 是必须的——两个节点 val 相同时，heapq 会去比较 ListNode 对象然后报错。Java 记得给 PriorityQueue 传比较器。
'''},

{"cat": "linked-list", "lc": 146, "t": "LRU 缓存", "d": "中等", "slug": "lru-cache", "md": r'''
**题目**：设计一个固定容量的缓存，`get`/`put` 都要 O(1)；容量满时淘汰**最久未使用**的数据（Least Recently Used）。

#### 💡 思路（白话）

- 两个需求 → 两个结构组合：
  - O(1) 查找 → **哈希表**（key → 节点）；
  - O(1) 维护「使用顺序」并删除最老的 → **双向链表**（最近用的放头部，尾部就是最久没用的；双向才能 O(1) 删除任意节点）。
- `get`：哈希表找到节点 → 把它**搬到链表头** → 返回值。
- `put`：已存在则更新值并搬到头；不存在则新建节点放头部，超容量就**删尾节点**（同时删哈希表）。
- 加 dummy head + dummy tail 两个哨兵，所有插入删除都不用判空。

#### ☕ Java

```java
class LRUCache {
    class Node { int key, val; Node prev, next; Node(int k, int v) { key = k; val = v; } }
    private final Map<Integer, Node> map = new HashMap<>();
    private final Node head = new Node(0, 0), tail = new Node(0, 0); // 哨兵
    private final int capacity;

    public LRUCache(int capacity) {
        this.capacity = capacity;
        head.next = tail; tail.prev = head;
    }
    public int get(int key) {
        Node node = map.get(key);
        if (node == null) return -1;
        moveToHead(node);
        return node.val;
    }
    public void put(int key, int value) {
        Node node = map.get(key);
        if (node != null) { node.val = value; moveToHead(node); return; }
        node = new Node(key, value);
        map.put(key, node);
        addToHead(node);
        if (map.size() > capacity) {       // 淘汰尾部（最久未用）
            Node last = tail.prev;
            remove(last);
            map.remove(last.key);
        }
    }
    private void remove(Node n) { n.prev.next = n.next; n.next.prev = n.prev; }
    private void addToHead(Node n) {
        n.next = head.next; n.prev = head;
        head.next.prev = n; head.next = n;
    }
    private void moveToHead(Node n) { remove(n); addToHead(n); }
}
```

#### 🐍 Python

```python
class LRUCache:
    def __init__(self, capacity: int):
        self.cap = capacity
        self.od = OrderedDict()          # 自带「记住插入顺序」的字典

    def get(self, key: int) -> int:
        if key not in self.od:
            return -1
        self.od.move_to_end(key)         # 搬到最近使用端
        return self.od[key]

    def put(self, key: int, value: int) -> None:
        if key in self.od:
            self.od.move_to_end(key)
        self.od[key] = value
        if len(self.od) > self.cap:
            self.od.popitem(last=False)  # 弹出最久未用
```

#### ⏱ 复杂度

get/put 均 O(1)，空间 O(capacity)。

**小白提示**：**面试手写代码出现率第一的题**，Java 版必须不看答案写出来（Node 里要存 key，否则删尾节点时不知道删哈希表哪个键——经典坑）。Python 的 OrderedDict 是作弊器，面试官多半会要求手写双向链表。
'''},
]
