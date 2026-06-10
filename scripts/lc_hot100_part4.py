# LeetCode Hot 100 讲义 · Part 4：二叉树(15)
PROBLEMS = [
{"cat": "binary-tree", "lc": 94, "t": "二叉树的中序遍历", "d": "简单", "slug": "binary-tree-inorder-traversal", "md": r'''
**题目**：返回二叉树的中序遍历（左 → 根 → 右）。

#### 💡 思路（白话）

- 中序 = 先把左子树全走完，再访问自己，再走右子树。递归写法三行搞定。
- 顺带记全：前序「根左右」、中序「左根右」、后序「左右根」——名字里的「前中后」指**根**的位置。
- 重要性质：**二叉搜索树（BST）的中序遍历是升序的**，后面好几道题都靠它。

#### ☕ Java

```java
class Solution {
    public List<Integer> inorderTraversal(TreeNode root) {
        List<Integer> res = new ArrayList<>();
        inorder(root, res);
        return res;
    }
    private void inorder(TreeNode node, List<Integer> res) {
        if (node == null) return;        // 递归出口
        inorder(node.left, res);         // 左
        res.add(node.val);               // 根
        inorder(node.right, res);        // 右
    }
}
```

#### 🐍 Python

```python
class Solution:
    def inorderTraversal(self, root: Optional[TreeNode]) -> List[int]:
        res = []
        def inorder(node):
            if not node:
                return
            inorder(node.left)
            res.append(node.val)
            inorder(node.right)
        inorder(root)
        return res
```

#### ⏱ 复杂度

时间 O(n)，空间 O(h)（h 为树高，递归栈）。

**小白提示**：树的第一课。把 `[1,2,3]` 组成的几种小树在纸上画出来，手动模拟递归过程（递归像「俄罗斯套娃」，进得去要出得来）。迭代写法（手动用栈）可以以后再补。
'''},

{"cat": "binary-tree", "lc": 104, "t": "二叉树的最大深度", "d": "简单", "slug": "maximum-depth-of-binary-tree", "md": r'''
**题目**：求二叉树的最大深度（根到最远叶子的节点数）。

#### 💡 思路（白话）

- 递归三步法的完美示范：
  1. **定义**：`maxDepth(node)` = 以 node 为根的树的最大深度；
  2. **出口**：空树深度为 0；
  3. **只想一层**：左子树深度和右子树深度都拿到了（黑盒），那我的深度 = 两者较大值 + 1（加自己这层）。
- 一行核心代码，却是所有树形递归的原型。

#### ☕ Java

```java
class Solution {
    public int maxDepth(TreeNode root) {
        if (root == null) return 0;
        return Math.max(maxDepth(root.left), maxDepth(root.right)) + 1;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def maxDepth(self, root: Optional[TreeNode]) -> int:
        if not root:
            return 0
        return max(self.maxDepth(root.left), self.maxDepth(root.right)) + 1
```

#### ⏱ 复杂度

时间 O(n)，空间 O(h)。

**小白提示**：写树的递归时**千万别在脑子里展开递归过程**（会绕晕），相信函数定义：「它就是能返回子树的深度」。这个思维转变是学会树题的关键一步。
'''},

{"cat": "binary-tree", "lc": 226, "t": "翻转二叉树", "d": "简单", "slug": "invert-binary-tree", "md": r'''
**题目**：把二叉树左右镜像翻转（每个节点的左右孩子互换）。

#### 💡 思路（白话）

- 递归：先把左右子树各自翻转好（黑盒），再交换自己的左右孩子。其实先交换再递归也行。
- 出口：空节点直接返回。

#### ☕ Java

```java
class Solution {
    public TreeNode invertTree(TreeNode root) {
        if (root == null) return null;
        TreeNode left = invertTree(root.left);    // 翻好左子树
        TreeNode right = invertTree(root.right);  // 翻好右子树
        root.left = right;                        // 交换
        root.right = left;
        return root;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def invertTree(self, root: Optional[TreeNode]) -> Optional[TreeNode]:
        if not root:
            return None
        root.left, root.right = self.invertTree(root.right), self.invertTree(root.left)
        return root
```

#### ⏱ 复杂度

时间 O(n)，空间 O(h)。

**小白提示**：这就是那道传说中「Homebrew 作者面 Google 没写出来」的题。本质就是「每个节点交换左右孩子」，用递归三步法套一下，两分钟写完。
'''},

{"cat": "binary-tree", "lc": 101, "t": "对称二叉树", "d": "简单", "slug": "symmetric-tree", "md": r'''
**题目**：判断二叉树是否轴对称（左右镜像）。

#### 💡 思路（白话）

- 「整棵树对称」转化为「**两棵子树互为镜像**」：左子树和右子树是镜像关系。
- 写辅助函数 `isMirror(a, b)`：a、b 互为镜像需要满足：
  1. a、b 都为空 → true；只有一个空 → false；
  2. `a.val == b.val`；
  3. **a 的左 和 b 的右**互为镜像，且 **a 的右 和 b 的左**互为镜像（注意交叉！）。

#### ☕ Java

```java
class Solution {
    public boolean isSymmetric(TreeNode root) {
        if (root == null) return true;
        return isMirror(root.left, root.right);
    }
    private boolean isMirror(TreeNode a, TreeNode b) {
        if (a == null && b == null) return true;
        if (a == null || b == null) return false;
        return a.val == b.val
            && isMirror(a.left, b.right)    // 外侧对外侧
            && isMirror(a.right, b.left);   // 内侧对内侧
    }
}
```

#### 🐍 Python

```python
class Solution:
    def isSymmetric(self, root: Optional[TreeNode]) -> bool:
        def mirror(a, b):
            if not a and not b:
                return True
            if not a or not b:
                return False
            return a.val == b.val and mirror(a.left, b.right) and mirror(a.right, b.left)
        return mirror(root.left, root.right) if root else True
```

#### ⏱ 复杂度

时间 O(n)，空间 O(h)。

**小白提示**：原函数参数不够用时，**另写一个参数更多的辅助函数**——这是树题的常用手法，后面「路径总和 III」「最大路径和」都会用到。
'''},

{"cat": "binary-tree", "lc": 543, "t": "二叉树的直径", "d": "简单", "slug": "diameter-of-binary-tree", "md": r'''
**题目**：求二叉树的直径——任意两节点之间最长路径的**边数**（不一定经过根）。

#### 💡 思路（白话）

- 任何一条路径都有一个「最高点」（拐点）。经过节点 node 的最长路径 = **左子树深度 + 右子树深度**。
- 所以：在求深度的递归里「顺手」干一件事——用 `左深 + 右深` 更新全局最大值。
- 这种「递归函数返回 A（深度），顺手用 A 算 B（直径）」的套路，是树题的高频模式，最大路径和（124）就是它的困难版。

#### ☕ Java

```java
class Solution {
    private int best = 0;
    public int diameterOfBinaryTree(TreeNode root) {
        depth(root);
        return best;
    }
    private int depth(TreeNode node) {
        if (node == null) return 0;
        int l = depth(node.left), r = depth(node.right);
        best = Math.max(best, l + r);     // 顺手更新：经过 node 的最长路径
        return Math.max(l, r) + 1;        // 本职工作：返回深度
    }
}
```

#### 🐍 Python

```python
class Solution:
    def diameterOfBinaryTree(self, root: Optional[TreeNode]) -> int:
        self.best = 0
        def depth(node):
            if not node:
                return 0
            l, r = depth(node.left), depth(node.right)
            self.best = max(self.best, l + r)
            return max(l, r) + 1
        depth(root)
        return self.best
```

#### ⏱ 复杂度

时间 O(n)，空间 O(h)。

**小白提示**：注意区分「函数返回值」和「答案」：返回的是**单边**深度（路径不能分叉着往上走），答案是**两边之和**。分清这两者，树形 DP 就入门了。
'''},

{"cat": "binary-tree", "lc": 102, "t": "二叉树的层序遍历", "d": "中等", "slug": "binary-tree-level-order-traversal", "md": r'''
**题目**：逐层从左到右遍历二叉树，每层一个列表。

#### 💡 思路（白话）

- **BFS 用队列**：根入队；每轮先记下当前队列长度 size（= 这一层的节点数），弹出 size 个节点处理，同时把它们的孩子入队——孩子们正好构成下一层。
- 「先记 size 再弹」是分层的关键，否则这层和下层会混在一起。

#### ☕ Java

```java
class Solution {
    public List<List<Integer>> levelOrder(TreeNode root) {
        List<List<Integer>> res = new ArrayList<>();
        if (root == null) return res;
        Queue<TreeNode> queue = new LinkedList<>();
        queue.offer(root);
        while (!queue.isEmpty()) {
            int size = queue.size();             // 这一层有几个
            List<Integer> level = new ArrayList<>();
            for (int i = 0; i < size; i++) {
                TreeNode node = queue.poll();
                level.add(node.val);
                if (node.left != null) queue.offer(node.left);
                if (node.right != null) queue.offer(node.right);
            }
            res.add(level);
        }
        return res;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def levelOrder(self, root: Optional[TreeNode]) -> List[List[int]]:
        if not root:
            return []
        res, queue = [], deque([root])
        while queue:
            level = []
            for _ in range(len(queue)):     # 只处理当前层
                node = queue.popleft()
                level.append(node.val)
                if node.left: queue.append(node.left)
                if node.right: queue.append(node.right)
            res.append(level)
        return res
```

#### ⏱ 复杂度

时间 O(n)，空间 O(n)。

**小白提示**：这个「按层 BFS」模板务必背熟——右视图、锯齿遍历、求每层平均值、腐烂的橘子……十几道题都是它换皮。
'''},

{"cat": "binary-tree", "lc": 108, "t": "将有序数组转换为二叉搜索树", "d": "简单", "slug": "convert-sorted-array-to-binary-search-tree", "md": r'''
**题目**：把升序数组转换为一棵**平衡**二叉搜索树（BST）。

#### 💡 思路（白话）

- BST 中序遍历是升序 ↔ 升序数组就是某棵 BST 的中序结果。
- 要平衡，就让左右子树节点数尽量相等 → **每次取中间元素当根**，左半边递归建左子树，右半边递归建右子树。
- 这是「分治建树」最简单的形态。

#### ☕ Java

```java
class Solution {
    public TreeNode sortedArrayToBST(int[] nums) {
        return build(nums, 0, nums.length - 1);
    }
    private TreeNode build(int[] nums, int left, int right) {
        if (left > right) return null;
        int mid = (left + right) / 2;          // 中间当根
        TreeNode root = new TreeNode(nums[mid]);
        root.left = build(nums, left, mid - 1);
        root.right = build(nums, mid + 1, right);
        return root;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def sortedArrayToBST(self, nums: List[int]) -> Optional[TreeNode]:
        def build(left, right):
            if left > right:
                return None
            mid = (left + right) // 2
            root = TreeNode(nums[mid])
            root.left = build(left, mid - 1)
            root.right = build(mid + 1, right)
            return root
        return build(0, len(nums) - 1)
```

#### ⏱ 复杂度

时间 O(n)，空间 O(log n)。

**小白提示**：建树类递归的固定形状：「**建根 → 递归建左 → 递归建右 → 返回根**」。记住这个形状，后面「从前序与中序构造二叉树」就是它的进阶。
'''},

{"cat": "binary-tree", "lc": 98, "t": "验证二叉搜索树", "d": "中等", "slug": "validate-binary-search-tree", "md": r'''
**题目**：判断一棵树是否是合法的二叉搜索树（左子树**所有**节点 < 根 < 右子树**所有**节点）。

#### 💡 思路（白话）

- **经典错误**：只检查「左孩子 < 根 < 右孩子」。反例：根 5 的右子树里藏了个 3——每对父子都合法，整棵树不合法。
- 正解一（区间法）：每个节点都有一个允许的取值范围 `(low, high)`。根是 (-∞, +∞)；往左走，上界收紧为父节点值；往右走，下界收紧。
- 正解二（中序法）：BST 中序遍历必须**严格升序**，中序走一遍检查即可。

#### ☕ Java

```java
class Solution {
    public boolean isValidBST(TreeNode root) {
        return check(root, Long.MIN_VALUE, Long.MAX_VALUE);
    }
    private boolean check(TreeNode node, long low, long high) {
        if (node == null) return true;
        if (node.val <= low || node.val >= high) return false; // 越界
        return check(node.left, low, node.val)     // 左：上界收紧
            && check(node.right, node.val, high);  // 右：下界收紧
    }
}
```

#### 🐍 Python

```python
class Solution:
    def isValidBST(self, root: Optional[TreeNode]) -> bool:
        def check(node, low, high):
            if not node:
                return True
            if not (low < node.val < high):
                return False
            return check(node.left, low, node.val) and check(node.right, node.val, high)
        return check(root, float('-inf'), float('inf'))
```

#### ⏱ 复杂度

时间 O(n)，空间 O(h)。

**小白提示**：Java 用 `long` 是因为测试数据里有 `Integer.MIN_VALUE/MAX_VALUE` 的节点。面试先主动说出那个经典错误再给正解，会显得你真懂。
'''},

{"cat": "binary-tree", "lc": 230, "t": "二叉搜索树中第 K 小的元素", "d": "中等", "slug": "kth-smallest-element-in-a-bst", "md": r'''
**题目**：求 BST 中第 k 小的元素。

#### 💡 思路（白话）

- BST 中序遍历 = 升序序列 → 第 k 小就是**中序遍历的第 k 个**。
- 不用真的存下整个序列：中序遍历时带个计数器，访问到第 k 个就记下答案、提前停止。

#### ☕ Java

```java
class Solution {
    private int count = 0, ans = 0;
    public int kthSmallest(TreeNode root, int k) {
        inorder(root, k);
        return ans;
    }
    private void inorder(TreeNode node, int k) {
        if (node == null || count >= k) return;  // 找到了就不再走
        inorder(node.left, k);
        if (++count == k) { ans = node.val; return; }
        inorder(node.right, k);
    }
}
```

#### 🐍 Python

```python
class Solution:
    def kthSmallest(self, root: Optional[TreeNode], k: int) -> int:
        stack, cur = [], root
        while stack or cur:           # 中序遍历的迭代写法
            while cur:
                stack.append(cur)
                cur = cur.left        # 一路向左
            cur = stack.pop()         # 弹出 = 按升序访问
            k -= 1
            if k == 0:
                return cur.val
            cur = cur.right
        return -1
```

#### ⏱ 复杂度

时间 O(h + k)，空间 O(h)。

**小白提示**：看到「BST + 第 k 小/大/排名」，条件反射想中序。第 k **大**则用「反中序」（右根左）。Python 版顺便展示了中序的迭代写法，值得学会。
'''},

{"cat": "binary-tree", "lc": 199, "t": "二叉树的右视图", "d": "中等", "slug": "binary-tree-right-side-view", "md": r'''
**题目**：从右边看二叉树，返回能看到的节点值（每层最右边的节点）。

#### 💡 思路（白话）

- 层序遍历（102 题模板）换皮：每层只收集**最后一个**节点。
- 也可以 DFS：按「根 → 右 → 左」顺序遍历，每到一个**新深度**，第一个到达的节点就是这层最右的。

#### ☕ Java

```java
class Solution {
    public List<Integer> rightSideView(TreeNode root) {
        List<Integer> res = new ArrayList<>();
        if (root == null) return res;
        Queue<TreeNode> queue = new LinkedList<>();
        queue.offer(root);
        while (!queue.isEmpty()) {
            int size = queue.size();
            for (int i = 0; i < size; i++) {
                TreeNode node = queue.poll();
                if (i == size - 1) res.add(node.val);   // 每层最后一个
                if (node.left != null) queue.offer(node.left);
                if (node.right != null) queue.offer(node.right);
            }
        }
        return res;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def rightSideView(self, root: Optional[TreeNode]) -> List[int]:
        res = []
        def dfs(node, depth):
            if not node:
                return
            if depth == len(res):      # 这一层第一次被访问
                res.append(node.val)
            dfs(node.right, depth + 1) # 先右后左
            dfs(node.left, depth + 1)
        dfs(root, 0)
        return res
```

#### ⏱ 复杂度

时间 O(n)，空间 O(n)。

**小白提示**：DFS 版里 `depth == len(res)` 判断「新一层」很巧：res 已有 d 层结果，深度 d 的第一个访问者就是右视图节点。两种写法都掌握，面试可以二选一。
'''},

{"cat": "binary-tree", "lc": 114, "t": "二叉树展开为链表", "d": "中等", "slug": "flatten-binary-tree-to-linked-list", "md": r'''
**题目**：把二叉树原地展开成「只用 right 指针的链表」，顺序为**前序遍历**。

#### 💡 思路（白话）

- 对每个有左孩子的节点：
  1. 找到**左子树的最右节点**（左子树前序的最后一个）；
  2. 把原来的右子树接到它的 right 上；
  3. 把整棵左子树搬到 right 位置，left 置空。
- 处理完当前节点就走向 right，继续处理。每个节点只被「找最右」访问一次，O(n)。

#### ☕ Java

```java
class Solution {
    public void flatten(TreeNode root) {
        TreeNode cur = root;
        while (cur != null) {
            if (cur.left != null) {
                TreeNode rightmost = cur.left;          // 1. 左子树最右节点
                while (rightmost.right != null) rightmost = rightmost.right;
                rightmost.right = cur.right;            // 2. 原右子树接过去
                cur.right = cur.left;                   // 3. 左子树搬到右边
                cur.left = null;
            }
            cur = cur.right;
        }
    }
}
```

#### 🐍 Python

```python
class Solution:
    def flatten(self, root: Optional[TreeNode]) -> None:
        cur = root
        while cur:
            if cur.left:
                rightmost = cur.left
                while rightmost.right:
                    rightmost = rightmost.right
                rightmost.right = cur.right
                cur.right = cur.left
                cur.left = None
            cur = cur.right
```

#### ⏱ 复杂度

时间 O(n)，空间 O(1)。

**小白提示**：为什么右子树接到「左子树最右节点」？因为前序顺序里，左子树走完后下一个就是右子树，而左子树前序最后一个节点正是它的最右节点。画个 6 节点的树走一遍就明白。
'''},

{"cat": "binary-tree", "lc": 105, "t": "从前序与中序遍历序列构造二叉树", "d": "中等", "slug": "construct-binary-tree-from-preorder-and-inorder-traversal", "md": r'''
**题目**：根据前序遍历和中序遍历结果，重建这棵二叉树（节点值不重复）。

#### 💡 思路（白话）

- 两个关键事实：
  1. **前序的第一个 = 根**；
  2. 在中序里找到根，**根左边是左子树的中序，右边是右子树的中序**——还能数出左子树有几个节点。
- 知道左子树大小后，前序也能切成「根 | 左子树前序 | 右子树前序」。两边递归建树即可。
- 用哈希表存「值 → 中序下标」，找根从 O(n) 变 O(1)。

#### ☕ Java

```java
class Solution {
    private Map<Integer, Integer> idx = new HashMap<>(); // 值 -> 中序下标
    private int[] preorder;

    public TreeNode buildTree(int[] preorder, int[] inorder) {
        this.preorder = preorder;
        for (int i = 0; i < inorder.length; i++) idx.put(inorder[i], i);
        return build(0, preorder.length - 1, 0, inorder.length - 1);
    }
    private TreeNode build(int preL, int preR, int inL, int inR) {
        if (preL > preR) return null;
        TreeNode root = new TreeNode(preorder[preL]);   // 前序第一个是根
        int mid = idx.get(preorder[preL]);              // 根在中序的位置
        int leftSize = mid - inL;                       // 左子树节点数
        root.left = build(preL + 1, preL + leftSize, inL, mid - 1);
        root.right = build(preL + leftSize + 1, preR, mid + 1, inR);
        return root;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def buildTree(self, preorder: List[int], inorder: List[int]) -> Optional[TreeNode]:
        idx = {v: i for i, v in enumerate(inorder)}
        def build(pre_l, pre_r, in_l, in_r):
            if pre_l > pre_r:
                return None
            root = TreeNode(preorder[pre_l])
            mid = idx[root.val]
            left_size = mid - in_l
            root.left = build(pre_l + 1, pre_l + left_size, in_l, mid - 1)
            root.right = build(pre_l + left_size + 1, pre_r, mid + 1, in_r)
            return root
        return build(0, len(preorder) - 1, 0, len(inorder) - 1)
```

#### ⏱ 复杂度

时间 O(n)，空间 O(n)。

**小白提示**：四个下标容易乱，先在纸上写出 `preorder = [根 | 左...| 右...]` 和 `inorder = [左... | 根 | 右...]` 的示意图，对照着填递归参数。「前序定根、中序分左右」一句话记住本题。
'''},

{"cat": "binary-tree", "lc": 437, "t": "路径总和 III", "d": "中等", "slug": "path-sum-iii", "md": r'''
**题目**：统计树中「节点值之和等于 targetSum」的路径数。路径必须**向下**走（父到子），但起点终点任意。

#### 💡 思路（白话）

- 把「根到当前节点」这条线看成一个数组，「向下的路径」就是这个数组的**后缀**——问题变成「和为 K 的子数组」（560 题）的树上版本！
- **前缀和 + 哈希表 + DFS**：DFS 时维护根到当前的前缀和 `cur`，map 记录「路径上出现过的前缀和 → 次数」。当前节点贡献的答案 = `map[cur - target]`。
- 关键一步：**回溯**——离开节点时要把它的前缀和从 map 里减掉（不能让别的分支用到本分支的前缀）。

#### ☕ Java

```java
class Solution {
    public int pathSum(TreeNode root, int targetSum) {
        Map<Long, Integer> pre = new HashMap<>();
        pre.put(0L, 1);                       // 空前缀
        return dfs(root, 0L, targetSum, pre);
    }
    private int dfs(TreeNode node, long cur, int target, Map<Long, Integer> pre) {
        if (node == null) return 0;
        cur += node.val;
        int res = pre.getOrDefault(cur - target, 0);   // 以本节点结尾的路径数
        pre.merge(cur, 1, Integer::sum);               // 登记
        res += dfs(node.left, cur, target, pre);
        res += dfs(node.right, cur, target, pre);
        pre.merge(cur, -1, Integer::sum);              // 回溯！撤销登记
        return res;
    }
}
```

#### 🐍 Python

```python
class Solution:
    def pathSum(self, root: Optional[TreeNode], targetSum: int) -> int:
        pre = defaultdict(int)
        pre[0] = 1
        def dfs(node, cur):
            if not node:
                return 0
            cur += node.val
            res = pre[cur - targetSum]
            pre[cur] += 1
            res += dfs(node.left, cur) + dfs(node.right, cur)
            pre[cur] -= 1                  # 回溯
            return res
        return dfs(root, 0)
```

#### ⏱ 复杂度

时间 O(n)，空间 O(n)。

**小白提示**：先把 560 题彻底搞懂再做这题，你会发现几乎是一样的代码。「离开节点时撤销修改」是回溯思想第一次正式登场，下个专题会大量出现。
'''},

{"cat": "binary-tree", "lc": 236, "t": "二叉树的最近公共祖先", "d": "中等", "slug": "lowest-common-ancestor-of-a-binary-tree", "md": r'''
**题目**：找节点 p 和 q 的最近公共祖先（LCA）——同时是两者祖先的最深节点（节点可以是自己的祖先）。

#### 💡 思路（白话）

- 给递归函数定个定义：`lca(node, p, q)` = 在 node 这棵子树里找 p、q 的 LCA；如果子树里只有其中一个，就返回那一个；都没有返回 null。
- 只想一层：
  - node 是空或正好是 p/q → 返回 node；
  - 左右子树分别递归，结果记 `left`、`right`；
  - **左右都有结果** → p、q 分居两侧，node 就是 LCA；
  - 只有一边有 → 返回那一边的结果。

#### ☕ Java

```java
class Solution {
    public TreeNode lowestCommonAncestor(TreeNode root, TreeNode p, TreeNode q) {
        if (root == null || root == p || root == q) return root;
        TreeNode left = lowestCommonAncestor(root.left, p, q);
        TreeNode right = lowestCommonAncestor(root.right, p, q);
        if (left != null && right != null) return root; // 分居两侧
        return (left != null) ? left : right;           // 都在一侧
    }
}
```

#### 🐍 Python

```python
class Solution:
    def lowestCommonAncestor(self, root: 'TreeNode', p: 'TreeNode', q: 'TreeNode') -> 'TreeNode':
        if not root or root is p or root is q:
            return root
        left = self.lowestCommonAncestor(root.left, p, q)
        right = self.lowestCommonAncestor(root.right, p, q)
        if left and right:
            return root
        return left or right
```

#### ⏱ 复杂度

时间 O(n)，空间 O(h)。

**小白提示**：代码只有 7 行但思维含量极高，面试高频。注意「p 是 q 的祖先」这种情况也被自然覆盖了：搜到 p 就直接返回，不用往下找 q（q 一定在 p 下面）。
'''},

{"cat": "binary-tree", "lc": 124, "t": "二叉树中的最大路径和", "d": "困难", "slug": "binary-tree-maximum-path-sum", "md": r'''
**题目**：路径 = 树中任意两节点间的通路（不能分叉），求路径上节点值之和的最大值（节点值可为负）。

#### 💡 思路（白话）

- 「二叉树的直径」（543）的进阶版，同一个套路：
  - 递归函数的**本职**：返回「从 node 出发**往下走单边**的最大和」（只能选左或右一边，因为路径不能分叉）；
  - **顺手**：用「左单边 + 自己 + 右单边」更新全局最大（node 作为路径的拐点）。
- 负数处理：子树单边和是负的就不要了，取 `max(0, 子树贡献)`——宁可不带。

#### ☕ Java

```java
class Solution {
    private int best = Integer.MIN_VALUE;
    public int maxPathSum(TreeNode root) {
        gain(root);
        return best;
    }
    private int gain(TreeNode node) {        // 从 node 往下单边的最大和
        if (node == null) return 0;
        int left = Math.max(gain(node.left), 0);   // 负贡献不要
        int right = Math.max(gain(node.right), 0);
        best = Math.max(best, left + node.val + right); // node 当拐点
        return node.val + Math.max(left, right);        // 只能带一边上去
    }
}
```

#### 🐍 Python

```python
class Solution:
    def maxPathSum(self, root: Optional[TreeNode]) -> int:
        self.best = float('-inf')
        def gain(node):
            if not node:
                return 0
            left = max(gain(node.left), 0)
            right = max(gain(node.right), 0)
            self.best = max(self.best, left + node.val + right)
            return node.val + max(left, right)
        gain(root)
        return self.best
```

#### ⏱ 复杂度

时间 O(n)，空间 O(h)。

**小白提示**：和 543 对照着看：返回值都是「单边」，更新答案都用「两边之和」。全是负数时答案是最大的那个负数（best 初始化为负无穷、`node.val` 必选，正好覆盖）。这题是树形 DP 的毕业考。
'''},
]
